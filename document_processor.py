"""
EduMind AI - Document Processing & Real Semantic Retrieval (RAG) Engine
Handles file uploads (PDF, PPT, PPTX up to 100 MB), text extraction,
page/slide level chunking with metadata, subject-isolated vector indexing (FAISS),
and semantic retrieval.
"""

import io
import os
import re
import json
import hashlib
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False

import config
import database
import gemini_client

logger = logging.getLogger("document_processor")


class DocumentProcessingError(Exception):
    """Raised when document parsing or extraction fails."""
    pass


class FileSizeExceededError(DocumentProcessingError):
    """Raised when file size exceeds maximum supported limit."""
    pass


# ==============================================================================
# 1. SUBJECT-ISOLATED FAISS / NUMPY VECTOR STORE
# ==============================================================================
class SubjectVectorStore:
    """
    Manages vector embeddings and chunk metadata isolated by Subject and User ID using FAISS
    with a graceful Numpy Cosine Similarity fallback if FAISS is unavailable.
    Guarantees that querying subject 'Java' only retrieves Java materials for that specific student.
    """

    def __init__(self, subject: str, dimension: int = 768, user_id: str = "user_default"):
        self.subject: str = subject.strip().title()
        self.dimension: int = dimension
        self.user_id: str = str(user_id)
        
        idx_dir = config.get_user_index_dir(self.user_id, self.subject)
        self.index_path: Path = idx_dir / "index.faiss"
        self.meta_path: Path = idx_dir / "meta.json"
        self.emb_path: Path = idx_dir / "emb.npy"

        self.index: Optional[Any] = None
        self.embeddings_matrix: Optional[np.ndarray] = None
        self.chunks: List[Dict[str, Any]] = []
        self._load_or_create()

    def _load_or_create(self) -> None:
        """Load existing index from disk or initialize new FAISS / Numpy store."""
        if FAISS_AVAILABLE and self.index_path.exists() and self.meta_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                logger.info("Loaded FAISS vector index for subject '%s' (%d chunks)", self.subject, len(self.chunks))
                return
            except Exception as e:
                logger.warning("Error loading FAISS index for subject '%s': %s. Rebuilding.", self.subject, str(e))

        # Fallback to Numpy embedding matrix
        if self.emb_path.exists() and self.meta_path.exists():
            try:
                self.embeddings_matrix = np.load(str(self.emb_path))
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                logger.info("Loaded Numpy vector store for subject '%s' (%d chunks)", self.subject, len(self.chunks))
                return
            except Exception as e:
                logger.warning("Error loading Numpy store for subject '%s': %s.", self.subject, str(e))

        if FAISS_AVAILABLE:
            try:
                self.index = faiss.IndexFlatIP(self.dimension)
            except Exception:
                self.index = None
        self.chunks = []

    def add_chunks(self, new_chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        """Add chunks and normalized embeddings to the subject vector index."""
        if not new_chunks or not embeddings:
            return

        matrix = np.array(embeddings, dtype="float32")
        # Normalize vectors for cosine similarity (inner product)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        matrix = matrix / norms

        if FAISS_AVAILABLE:
            if self.index is None:
                self.index = faiss.IndexFlatIP(matrix.shape[1])
            self.index.add(matrix)

        if self.embeddings_matrix is None:
            self.embeddings_matrix = matrix
        else:
            self.embeddings_matrix = np.vstack([self.embeddings_matrix, matrix])

        self.chunks.extend(new_chunks)
        self._save()

    def _save(self) -> None:
        """Persist index and chunk metadata to disk."""
        config.INDEXES_DIR.mkdir(parents=True, exist_ok=True)
        if FAISS_AVAILABLE and self.index is not None:
            try:
                faiss.write_index(self.index, str(self.index_path))
            except Exception as e:
                logger.warning("Failed to save FAISS index: %s", str(e))

        if self.embeddings_matrix is not None:
            np.save(str(self.emb_path), self.embeddings_matrix)

        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2)

def normalize_query(query: str) -> str:
    """
    Remove conversational filler phrases ('tell me about', 'explain', 'in pdf', 'from document')
    to extract core search keywords while preserving technical terms.
    """
    if not query or not query.strip():
        return ""

    q = query.strip()
    
    # 1. Strip common conversational prefixes (case-insensitive)
    prefixes = [
        r"^\b(tell\s+me\s+about\s+the|tell\s+mee\s+about\s+the|tell\s+me\s+about|tell\s+mee\s+about|tell\s+me|tell\s+mee|explain\s+to\s+me|explain\s+about|explain\s+the|explain|what\s+is\s+a|what\s+is\s+an|what\s+is|what\s+are\s+the|what\s+are|give\s+me\s+an?\s+overview\s+of|give\s+mee\s+an?\s+overview\s+of|give\s+me|give\s+mee|can\s+you\s+explain|can\s+you\s+tell\s+me\s+about|can\s+you\s+tell\s+mee\s+about|describe|show\s+me|show\s+mee)\b\s*",
    ]
    
    # 2. Strip common conversational suffixes (case-insensitive)
    suffixes = [
        r"\s*\b(in\s+this\s+pdf|in\s+the\s+pdf|in\s+pdf|from\s+this\s+pdf|from\s+the\s+pdf|from\s+pdf|in\s+this\s+document|in\s+the\s+document|in\s+document|from\s+this\s+document|from\s+the\s+document|from\s+document|uploaded\s+pdf|uploaded\s+document|uploaded\s+material|uploaded\s+notes|in\s+the\s+uploaded\s+material|in\s+the\s+uploaded\s+pdf|in\s+uploaded\s+pdf|pdf|document|notes|material|slides|ppt|pptx|file)\b[\?\.\!\s]*$",
    ]

    cleaned = q
    for p in prefixes:
        cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE)
    for s in suffixes:
        cleaned = re.sub(s, "", cleaned, flags=re.IGNORECASE)

    cleaned = cleaned.strip("? .! \t\n")
    # If cleaning stripped everything (e.g. user literally asked "tell me about the pdf"), return original query
    return cleaned if len(cleaned) >= 2 else q.strip("? .!")


class SubjectVectorStore:
    """Vector store for a single subject and user context."""

    def __init__(self, subject: str, user_id: str = "user_default"):
        self.subject = subject.strip().title()
        self.user_id = user_id
        safe_subj = re.sub(r"[^\w\-]", "_", self.subject)
        safe_user = re.sub(r"[^\w\-]", "_", self.user_id)

        self.store_dir = config.INDEXES_DIR / safe_user / safe_subj
        self.index_path = self.store_dir / "index.faiss"
        self.meta_path = self.store_dir / "meta.json"
        self.emb_path = self.store_dir / "emb.npy"

        self.dimension = 768
        self.index = None
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings_matrix: Optional[np.ndarray] = None
        self._load()

    def _load(self) -> None:
        """Load vector store from disk if present."""
        if self.emb_path.exists() and self.meta_path.exists():
            try:
                self.embeddings_matrix = np.load(str(self.emb_path))
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                logger.info("Loaded Numpy vector store for subject '%s' (%d chunks)", self.subject, len(self.chunks))
                return
            except Exception as e:
                logger.warning("Error loading Numpy store for subject '%s': %s.", self.subject, str(e))

        if FAISS_AVAILABLE:
            try:
                self.index = faiss.IndexFlatIP(self.dimension)
            except Exception:
                self.index = None
        self.chunks = []

    def add_chunks(self, new_chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        """Add chunks and normalized embeddings to the subject vector index."""
        if not new_chunks or not embeddings:
            return

        matrix = np.array(embeddings, dtype="float32")
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        matrix = matrix / norms

        if FAISS_AVAILABLE:
            if self.index is None:
                self.index = faiss.IndexFlatIP(matrix.shape[1])
            self.index.add(matrix)

        if self.embeddings_matrix is None:
            self.embeddings_matrix = matrix
        else:
            self.embeddings_matrix = np.vstack([self.embeddings_matrix, matrix])

        self.chunks.extend(new_chunks)
        self._save()

    def _save(self) -> None:
        """Persist index and chunk metadata to disk."""
        self.store_dir.mkdir(parents=True, exist_ok=True)
        if FAISS_AVAILABLE and self.index is not None:
            try:
                faiss.write_index(self.index, str(self.index_path))
            except Exception as e:
                logger.warning("Failed to save FAISS index: %s", str(e))

        if self.embeddings_matrix is not None:
            np.save(str(self.emb_path), self.embeddings_matrix)

        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = config.TOP_K,
        doc_id: Optional[str] = None,
        doc_name: Optional[str] = None,
        query_text: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Perform HYBRID (Vector + Keyword) search using query vector and text.
        If doc_id or doc_name is provided, filter results STRICTLY to matching document chunks.
        """
        if not self.chunks:
            return []

        valid_indices = None
        if doc_id or doc_name:
            clean_id = str(doc_id).strip() if doc_id else ""
            clean_name = str(doc_name).strip().lower() if doc_name else ""
            clean_stem = Path(clean_name).stem.lower() if ("." in clean_name and len(clean_name) > 3) else clean_name

            matching = []
            for idx, c in enumerate(self.chunks):
                c_id = str(c.get("doc_id", ""))
                c_fn = str(c.get("filename") or c.get("doc_name", "")).lower()

                if (clean_id and c_id == clean_id) or \
                   (clean_name and (c_fn == clean_name or (clean_stem and len(clean_stem) >= 3 and clean_stem in c_fn))):
                    matching.append(idx)

            if matching:
                valid_indices = set(matching)
            else:
                logger.info("Vector store filter for doc_id='%s' doc_name='%s' matched 0 chunks.", doc_id, doc_name)
                return []

        q_vec = np.array([query_embedding], dtype="float32")
        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec = q_vec / norm

        norm_q = normalize_query(query_text).lower() if query_text else ""
        raw_tokens = [w for w in re.findall(r"\w{2,}", norm_q)]
        
        expanded_keywords = set(raw_tokens)
        for t in raw_tokens:
            if t.endswith("s") and len(t) > 3:
                expanded_keywords.add(t[:-1])
            elif not t.endswith("s"):
                expanded_keywords.add(t + "s")

        if "loop" in expanded_keywords or "loops" in expanded_keywords:
            expanded_keywords.update(["loop", "loops", "for loop", "while loop", "do-while", "do while", "iteration"])

        idx_list = sorted(list(valid_indices)) if valid_indices is not None else list(range(len(self.chunks)))
        
        # 1. Vector similarity scores
        vector_scores = np.zeros(len(idx_list), dtype="float32")
        if self.embeddings_matrix is not None and len(self.embeddings_matrix) > 0:
            sub_matrix = self.embeddings_matrix[idx_list]
            vector_scores = np.dot(sub_matrix, q_vec.T).flatten()

        # 2. Keyword match scores (Term Frequency + Title Boost)
        keyword_scores = np.zeros(len(idx_list), dtype="float32")
        for pos, orig_idx in enumerate(idx_list):
            chunk = self.chunks[orig_idx]
            chunk_text = chunk.get("text", "").lower()
            sec_title = str(chunk.get("section_title", "")).lower()
            kw_score = 0.0
            
            # Exact normalized query phrase match
            if norm_q and norm_q in chunk_text:
                kw_score += 3.0

            # Expanded topic keyword matches (term frequency)
            for kw in expanded_keywords:
                cnt = chunk_text.count(kw)
                if cnt > 0:
                    kw_score += min(cnt, 5) * 1.0
                    if kw in sec_title:
                        kw_score += 2.0

            keyword_scores[pos] = min(kw_score / 5.0, 1.0)

        # 3. Hybrid Combination (0.3 Vector + 0.7 Keyword)
        hybrid_scores = 0.3 * vector_scores + 0.7 * keyword_scores
        
        k = min(top_k, len(hybrid_scores))
        top_sub_indices = np.argsort(hybrid_scores)[::-1][:k]

        results = []
        for sub_idx in top_sub_indices:
            if hybrid_scores[sub_idx] > 0.02:
                orig_idx = idx_list[sub_idx]
                chunk = dict(self.chunks[orig_idx])
                chunk["score"] = float(hybrid_scores[sub_idx])
                results.append(chunk)

        return results


# Cache of loaded vector stores by subject
_VECTOR_STORES: Dict[str, SubjectVectorStore] = {}


def get_subject_vector_store(subject: str, user_id: str = "user_default") -> SubjectVectorStore:
    """Retrieve or create the user-and-subject isolated vector store."""
    subj_norm = subject.strip().title()
    key = f"{user_id}_{subj_norm}"
    if key not in _VECTOR_STORES:
        _VECTOR_STORES[key] = SubjectVectorStore(subj_norm, user_id=user_id)
    return _VECTOR_STORES[key]


# ==============================================================================
# 2. DOCUMENT PARSING & CHUNKING ENGINE
# ==============================================================================
def process_uploaded_file(
    file_bytes: bytes,
    filename: str,
    subject: str = config.DEFAULT_SUBJECT,
    user_id: str = "user_default"
) -> Dict[str, Any]:
    """
    Parse uploaded PDF, PPT, or PPTX bytes up to MAX_FILE_SIZE_MB.
    Extracts complete text, performs chunking with page/slide metadata,
    generates embeddings, and registers in subject vector index, MongoDB Atlas, and SQLite DB.
    """
    file_size_bytes = len(file_bytes)
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

    if file_size_bytes > config.MAX_FILE_SIZE_BYTES:
        raise FileSizeExceededError(
            f"File size ({file_size_mb} MB) exceeds maximum supported limit of {config.MAX_FILE_SIZE_MB} MB."
        )

    file_ext = Path(filename).suffix.lower().lstrip(".")
    if file_ext not in config.SUPPORTED_FILE_TYPES:
        raise DocumentProcessingError(
            f"Unsupported file format '.{file_ext}'. Supported formats: {', '.join(config.SUPPORTED_FILE_TYPES).upper()}"
        )

    # Compute content hash for deduplication
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    doc_id = f"doc_{file_hash[:12]}"
    subj_norm = subject.strip().title()

    # Save raw file to user-specific uploads directory data/uploads/{user_id}/
    user_upload_dir = config.get_user_upload_dir(user_id)
    saved_file_path = user_upload_dir / f"{doc_id}_{filename}"
    with open(saved_file_path, "wb") as f:
        f.write(file_bytes)

    # Extract chunks unit-by-unit
    chunks: List[Dict[str, Any]] = []
    if file_ext == "pdf":
        chunks = _extract_pdf_chunks(file_bytes, filename, subj_norm, doc_id)
    elif file_ext in ["ppt", "pptx"]:
        chunks = _extract_pptx_chunks(file_bytes, filename, subj_norm, doc_id)

    if not chunks:
        logger.warning("No readable text extracted from %s", filename)

    # Generate embeddings for semantic retrieval
    chunk_texts = [c["text"] for c in chunks]
    embeddings = gemini_client.generate_embeddings(chunk_texts) if chunk_texts else []

    # Store in user-specific subject vector index
    if chunks and embeddings:
        v_store = get_subject_vector_store(subj_norm, user_id=user_id)
        v_store.add_chunks(chunks, embeddings)

    # Generate automatic AI overview of uploaded material
    overview = generate_material_overview(chunks, filename, subj_norm, len(chunks))
    database.save_material_overview(doc_id, filename, subj_norm, overview)

    total_chars = sum(len(c.get("text", "")) for c in chunks if c.get("status") != "OCR_REQUIRED")
    doc_status = "READY" if total_chars > 50 else "OCR_REQUIRED"

    doc_data = {
        "user_id": str(user_id),
        "doc_id": doc_id,
        "filename": filename,
        "file_hash": file_hash,
        "subject": subj_norm,
        "file_size_mb": file_size_mb,
        "file_type": file_ext.upper(),
        "total_units": len(chunks),
        "extracted_chars": total_chars,
        "status": doc_status,
        "chunks": chunks,
        "overview": overview
    }

    # Save processed JSON and database record
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    processed_path = config.PROCESSED_DIR / f"{doc_id}.json"
    with open(processed_path, "w", encoding="utf-8") as f:
        json.dump(doc_data, f, indent=2)

    import mongodb
    mongodb.save_document(user_id, doc_data, str(saved_file_path))
    database.save_document_record(doc_data, str(saved_file_path))

    logger.info(
        "Processed and indexed %s for user '%s' subject '%s' (%s MB, %d chunks)",
        filename, user_id, subj_norm, file_size_mb, len(chunks)
    )
    return doc_data


def strip_html_tags(text: str) -> str:
    """Strip raw HTML/script tags from a string to extract plain text."""
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    # Remove script tags and contents
    text = re.sub(
        r"<script\b[^>]*>.*?</script\s*>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    # Strip HTML tags
    cleaned = re.sub(r'<[^>]+>', '', text)
    # Unescape common HTML entities
    cleaned = cleaned.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
    return cleaned.strip()


def generate_material_overview(chunks: List[Dict[str, Any]], filename: str, subject: str, total_units: int = 1) -> Dict[str, Any]:
    """
    Automatically generate a structured academic overview of uploaded material using Gemini AI.
    Contains: Document title, Subject, Number of pages/slides, Main topics, Key concepts, Recommended order, Exam focus.
    Grounded STRICTLY in the uploaded material.
    """
    clean_fn = strip_html_tags(filename)
    clean_sub = strip_html_tags(subject)

    if not chunks:
        return {
            "document_title": clean_fn,
            "subject": clean_sub,
            "total_units": total_units,
            "main_topics": ["General Overview"],
            "key_concepts": ["Course Notes"],
            "recommended_order": ["Read through the document"],
            "exam_points": ["Review key terms"]
        }

    context_text = "\n".join([f"[{c.get('unit_label', 'Page')}] {c.get('text', '')}" for c in chunks[:15]])
    if len(context_text) > 8000:
        context_text = context_text[:8000]

    prompt = f"""
Analyze the following uploaded study material for the subject '{clean_sub}'.
DOCUMENT FILENAME: {clean_fn}
EXTRACTED CONTENT:
{context_text}

Generate a comprehensive academic overview grounded STRICTLY in this material. Do NOT invent topics not present in the content.
Do NOT output raw HTML tags or wrap list items in HTML markup. Return ONLY clean JSON.

OUTPUT JSON FORMAT:
{{
  "main_topics": ["Topic 1", "Topic 2", "Topic 3", "Topic 4"],
  "key_concepts": ["Concept 1", "Concept 2", "Concept 3"],
  "recommended_order": ["1. Topic 1", "2. Topic 2", "3. Topic 3"],
  "exam_points": ["Exam Focus Point 1", "Exam Focus Point 2"]
}}
"""
    try:
        data = gemini_client.generate_json_response(prompt)
        if isinstance(data, str):
            import json
            try:
                data = json.loads(data)
            except Exception:
                data = {}

        def sanitize_list(items: Any, default: List[str]) -> List[str]:
            if isinstance(items, list):
                res = [strip_html_tags(str(x)) for x in items if strip_html_tags(str(x))]
                return res if res else default
            elif isinstance(items, str) and items.strip():
                clean = strip_html_tags(items)
                return [clean] if clean else default
            return default

        main_topics = sanitize_list(data.get("main_topics"), ["Overview of " + clean_fn])
        key_concepts = sanitize_list(data.get("key_concepts"), ["Core Concepts"])
        recommended_order = sanitize_list(data.get("recommended_order"), [f"{i+1}. {t}" for i, t in enumerate(main_topics)])
        exam_points = sanitize_list(data.get("exam_points"), ["Key definitions and formulas"])

    except Exception as e:
        logger.warning("Failed to generate Gemini overview: %s. Using heuristic fallback.", str(e))
        content_headings = []
        for c in chunks:
            st_title = c.get("section_title", "")
            if st_title and not st_title.startswith("Page ") and not st_title.startswith("Slide "):
                content_headings.append(strip_html_tags(st_title))
            txt = c.get("text", "")
            lines = [l.strip() for l in txt.split("\n") if l.strip() and 5 <= len(l.strip()) <= 80]
            for l in lines[:2]:
                if not any(l.lower().startswith(p) for p in ["page ", "slide ", "http", "www"]):
                    content_headings.append(strip_html_tags(l))
        
        main_topics = list(dict.fromkeys(content_headings))[:5]
        if not main_topics:
            main_topics = [f"Core Topics in {clean_fn}"]
        key_concepts = list(dict.fromkeys(content_headings[5:10])) if len(content_headings) > 5 else [f"Key concepts in {clean_fn}"]
        recommended_order = [f"{i+1}. {t}" for i, t in enumerate(main_topics)]
        exam_points = [f"Study {t} for exams" for t in main_topics[:3]]

    return {
        "document_title": clean_fn,
        "subject": clean_sub,
        "total_units": total_units,
        "main_topics": main_topics,
        "key_concepts": key_concepts,
        "recommended_order": recommended_order,
        "exam_points": exam_points
    }


def process_study_space_file(
    file_bytes: bytes,
    filename: str,
    space_id: str,
    subject: str,
    uploaded_by: str,
    uploaded_by_name: str
) -> Dict[str, Any]:
    """
    Process study space file and store in isolated vector index for this space (`user_id=space_{space_id}`).
    """
    file_size_bytes = len(file_bytes)
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
    file_ext = Path(filename).suffix.lower().lstrip(".")

    file_hash = hashlib.sha256(file_bytes).hexdigest()
    doc_id = f"sdoc_{space_id[:8]}_{file_hash[:8]}"
    subj_norm = subject.strip().title()

    space_dir = config.DATA_DIR / "uploads" / "study_spaces" / space_id
    space_dir.mkdir(parents=True, exist_ok=True)
    saved_path = space_dir / f"{doc_id}_{filename}"
    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    chunks: List[Dict[str, Any]] = []
    if file_ext == "pdf":
        chunks = _extract_pdf_chunks(file_bytes, filename, subj_norm, doc_id)
    elif file_ext in ["ppt", "pptx"]:
        chunks = _extract_pptx_chunks(file_bytes, filename, subj_norm, doc_id)

    chunk_texts = [c["text"] for c in chunks]
    embeddings = gemini_client.generate_embeddings(chunk_texts) if chunk_texts else []

    # Vector store ISOLATED specifically for this Study Space using user_id=f"space_{space_id}"
    space_user_id = f"space_{space_id}"
    if chunks and embeddings:
        v_store = get_subject_vector_store(subj_norm, user_id=space_user_id)
        v_store.add_chunks(chunks, embeddings)

    doc_data = {
        "doc_id": doc_id,
        "space_id": space_id,
        "uploaded_by": uploaded_by,
        "uploaded_by_name": uploaded_by_name,
        "filename": filename,
        "file_hash": file_hash,
        "subject": subj_norm,
        "file_size_mb": file_size_mb,
        "file_type": file_ext.upper(),
        "total_units": len(chunks),
        "chunks": chunks
    }

    # Generate automatic overview for Study Space document
    overview = generate_material_overview(chunks, filename, subj_norm, len(chunks))
    doc_data["overview"] = overview
    database.save_material_overview(doc_id, filename, subj_norm, overview)

    database.save_study_space_document(
        doc_id=doc_id,
        space_id=space_id,
        uploaded_by=uploaded_by,
        uploaded_by_name=uploaded_by_name,
        filename=filename,
        file_type=file_ext.upper(),
        file_size_mb=file_size_mb,
        total_units=len(chunks),
        storage_path=str(saved_path)
    )

    return doc_data



def _extract_pdf_chunks(file_bytes: bytes, filename: str, subject: str, doc_id: str) -> List[Dict[str, Any]]:
    """Extract text from PDF using pypdf, preserving page metadata and detecting scanned PDFs."""
    import pypdf

    chunks = []
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            try:
                text = (page.extract_text() or "").strip()
            except Exception:
                text = ""
            if text:
                sub_chunks = _split_text_into_chunks(text, max_chars=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP)
                for sub_idx, sub_text in enumerate(sub_chunks):
                    label = f"Page {page_num}" if len(sub_chunks) == 1 else f"Page {page_num} (Part {sub_idx + 1})"
                    chunk_id = f"{doc_id}_p{page_num}_{sub_idx}"
                    chunks.append({
                        "chunk_id": chunk_id,
                        "doc_id": doc_id,
                        "doc_name": filename,
                        "filename": filename,
                        "unit_label": label,
                        "unit_num": page_num,
                        "subject": subject,
                        "section_title": f"Page {page_num}",
                        "text": sub_text
                    })
    except Exception as e:
        logger.warning("Error reading PDF %s with pypdf: %s. Marking as OCR_REQUIRED.", filename, str(e))

    if not chunks:
        logger.warning("PDF '%s' extracted 0 text characters using pypdf. Document may be scanned or image-only.", filename)
        chunks.append({
            "chunk_id": f"{doc_id}_ocr_required",
            "doc_id": doc_id,
            "doc_name": filename,
            "filename": filename,
            "unit_label": "Page 1 (Scanned)",
            "unit_num": 1,
            "subject": subject,
            "section_title": "Scanned Document Notice",
            "text": f"Document '{filename}' appears to be a scanned PDF or image without selectable text. Status: OCR_REQUIRED.",
            "status": "OCR_REQUIRED"
        })

    return chunks


def _extract_pptx_chunks(file_bytes: bytes, filename: str, subject: str, doc_id: str) -> List[Dict[str, Any]]:
    """Extract text from PPT/PPTX using python-pptx, preserving slide metadata."""
    import pptx

    chunks = []
    try:
        prs = pptx.Presentation(io.BytesIO(file_bytes))
        for slide_idx, slide in enumerate(prs.slides):
            slide_num = slide_idx + 1
            slide_texts = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    slide_texts.append(shape.text.strip())

            full_slide_text = "\n".join(slide_texts).strip()
            if full_slide_text:
                sub_chunks = _split_text_into_chunks(full_slide_text, max_chars=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP)
                for sub_idx, sub_text in enumerate(sub_chunks):
                    label = f"Slide {slide_num}" if len(sub_chunks) == 1 else f"Slide {slide_num} (Part {sub_idx + 1})"
                    chunk_id = f"{doc_id}_s{slide_num}_{sub_idx}"
                    chunks.append({
                        "chunk_id": chunk_id,
                        "doc_id": doc_id,
                        "doc_name": filename,
                        "filename": filename,
                        "unit_label": label,
                        "unit_num": slide_num,
                        "subject": subject,
                        "section_title": f"Slide {slide_num}",
                        "text": sub_text
                    })
    except Exception as e:
        logger.error("Error reading PPTX %s: %s", filename, str(e))
        raise DocumentProcessingError(f"Failed to parse Presentation file '{filename}': {str(e)}") from e

    return chunks


def _split_text_into_chunks(text: str, max_chars: int = 800, overlap: int = 150) -> List[str]:
    """Split text into overlapping chunks of max_chars length."""
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += max_chars - overlap

    return chunks


# ==============================================================================
# 3. SEMANTIC RETRIEVAL ENGINE (SUBJECT ISOLATED)
# ==============================================================================
def search_documents(
    documents: Optional[List[Dict[str, Any]]] = None,
    query: str = "",
    subject: str = config.DEFAULT_SUBJECT,
    top_k: int = config.TOP_K,
    user_id: str = "user_default",
    doc_id: Optional[str] = None,
    doc_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Perform semantic search for query within course materials.
    Searches across active document (if specified), or across all documents in subject,
    with fallback to all user documents across subjects if no subject match is found.
    """
    if not query or not query.strip():
        return []

    subj_norm = subject.strip().title()
    query_clean = query.strip()
    query_lower = query_clean.lower()

    target_doc_id = doc_id
    target_doc_name = doc_name

    # 1. EXPLICIT DOCUMENT NAME REFERENCE MATCHING IN QUERY
    if documents:
        for d in documents:
            fn = d.get("filename", "").lower()
            fn_stem = Path(fn).stem.lower() if ("." in fn and len(fn) > 3) else fn
            if (len(fn_stem) >= 3 and fn_stem in query_lower) or (fn and fn in query_lower):
                target_doc_id = d.get("doc_id")
                target_doc_name = d.get("filename")
                logger.info("[RAG] Query explicitly referenced document: '%s' (ID: %s)", target_doc_name, target_doc_id)
                break

    # 2. OVERVIEW / GENERAL DOCUMENT QUERY DETECTION
    norm_topic = normalize_query(query_clean)
    norm_lower = norm_topic.lower().strip()

    pure_overview_phrases = [
        "overview of the pdf", "overview of pdf", "overview of document", "document overview", "pdf overview",
        "summary of the pdf", "summary of pdf", "summary of document", "document summary", "pdf summary",
        "what is this pdf about", "what is this document about", "what is this pdf", "what is this document",
        "explain this pdf", "explain this document", "tell me about this pdf", "tell me about this document",
        "tell mee about this pdf", "tell mee about pdf", "tell me about pdf", "tell me about document",
        "tell mee about document", "tell me about the pdf", "tell mee about the pdf", "tell me about the document",
        "about the pdf", "about the document", "general overview", "overall summary"
    ]

    is_overview_q = False
    if norm_lower in ["overview", "summary", "this pdf", "this document", "pdf", "document"] or any(p in query_lower for p in pure_overview_phrases):
        stop_words = ["pdf", "document", "overview", "summary", "this", "the", "about", "general", "uploaded", "material", "notes", "tell", "me", "mee", "explain", "give", "show", "details", "info", "information"]
        topic_words = [w for w in re.findall(r"\w+", norm_lower) if w not in stop_words]
        if not topic_words:
            is_overview_q = True

    # Resolve target document object ONLY if explicit target document was set
    target_doc_obj = None
    if documents and (target_doc_id or target_doc_name):
        if target_doc_id:
            target_doc_obj = next((d for d in documents if d.get("doc_id") == target_doc_id), None)
        if not target_doc_obj and target_doc_name:
            target_doc_obj = next((d for d in documents if d.get("filename", "").lower() == target_doc_name.lower()), None)

    # 3. IF PURE OVERVIEW QUERY AND A TARGET DOC IS SPECIFIED (OR LATEST DOC FOR OVERVIEW ONLY)
    if is_overview_q:
        overview_doc = target_doc_obj or (documents[-1] if documents else None)
        if overview_doc:
            rep_chunks = []
            ov = overview_doc.get("overview")
            if ov and isinstance(ov, dict):
                ov_text = (
                    f"DOCUMENT OVERVIEW & SUMMARY for {overview_doc.get('filename')}:\n"
                    f"Main Topics: {', '.join(ov.get('main_topics', []))}\n"
                    f"Key Concepts: {', '.join(ov.get('key_concepts', []))}\n"
                    f"Recommended Order: {', '.join(ov.get('recommended_order', []))}\n"
                    f"Exam Focus Points: {', '.join(ov.get('exam_points', []))}"
                )
                rep_chunks.append({
                    "chunk_id": f"{overview_doc.get('doc_id')}_overview",
                    "doc_id": overview_doc.get("doc_id"),
                    "doc_name": overview_doc.get("filename"),
                    "filename": overview_doc.get("filename"),
                    "unit_label": "Document Overview",
                    "unit_num": 0,
                    "subject": subj_norm,
                    "section_title": "Overview",
                    "text": ov_text,
                    "score": 1.0
                })

            doc_chunks = overview_doc.get("chunks", [])
            for c in doc_chunks[:6]:
                rep_chunks.append(dict(c))

            if rep_chunks:
                logger.info("[RAG] OVERVIEW QUERY MATCH | Target Doc: %s (%s) | Returned %d overview chunks.", overview_doc.get('filename'), overview_doc.get('doc_id'), len(rep_chunks))
                return rep_chunks[:top_k]

    # 4. HYBRID VECTOR + KEYWORD SEARCH WITH MULTI-TIER FALLBACK
    search_term = norm_topic if norm_topic else query_clean
    query_embeddings = gemini_client.generate_embeddings([search_term])
    emb_vector = query_embeddings[0] if query_embeddings else [0.0]*768

    results = []

    # TIER A: Primary subject vector store search
    v_store = get_subject_vector_store(subj_norm, user_id=user_id)
    if v_store.chunks:
        results = v_store.search(
            query_embedding=emb_vector,
            top_k=top_k,
            doc_id=target_doc_id,
            doc_name=target_doc_name,
            query_text=search_term
        )

    # TIER B: If no results in current subject and no explicit document filter was specified,
    # search across all other subject vector stores for this user
    if not results and not target_doc_id and not target_doc_name:
        safe_user = re.sub(r"[^\w\-]", "_", str(user_id))
        user_idx_base = config.INDEXES_DIR / safe_user
        if user_idx_base.exists():
            for subj_dir in user_idx_base.iterdir():
                if subj_dir.is_dir() and subj_dir.name != re.sub(r"[^\w\-]", "_", subj_norm):
                    other_subj = subj_dir.name.replace("_", " ")
                    other_vstore = get_subject_vector_store(other_subj, user_id=user_id)
                    if other_vstore.chunks:
                        res = other_vstore.search(
                            query_embedding=emb_vector,
                            top_k=top_k,
                            query_text=search_term
                        )
                        results.extend(res)

            if results:
                unique_res = {}
                for c in results:
                    cid = c.get("chunk_id") or f"{c.get('doc_id')}_{c.get('unit_num')}"
                    if cid not in unique_res or c.get("score", 0.0) > unique_res[cid].get("score", 0.0):
                        unique_res[cid] = c
                results = sorted(unique_res.values(), key=lambda x: x.get("score", 0.0), reverse=True)[:top_k]

    # TIER C: IN-MEMORY HYBRID FALLBACK FILTERED BY TARGET DOCUMENT OR ALL DOCUMENTS
    if not results and documents:
        in_mem_chunks = []
        for d in documents:
            if target_doc_id and d.get("doc_id") != target_doc_id:
                continue
            if not target_doc_id and target_doc_name and d.get("filename", "").lower() != target_doc_name.lower():
                continue
            for c in d.get("chunks", []):
                in_mem_chunks.append(c)

        if in_mem_chunks:
            search_lower = search_term.lower()
            keywords = [w for w in re.findall(r"\w{2,}", search_lower)]
            scored = []
            for c in in_mem_chunks:
                c_text = c.get("text", "").lower()
                kw_score = 0.0
                if search_lower in c_text:
                    kw_score += 2.0
                for kw in keywords:
                    if kw in c_text:
                        kw_score += 0.5
                scored.append((kw_score, c))
            scored.sort(key=lambda x: x[0], reverse=True)
            results = [c for score, c in scored[:top_k] if score > 0.1]

    # DIAGNOSTIC LOGGING METRICS
    retrieved_ids = list(dict.fromkeys(c.get("doc_id") for c in results))
    scores = [round(c.get("score", 0.0), 3) for c in results[:3]]
    sources = [f"{c.get('filename', 'Doc')} — {c.get('unit_label', 'Page 1')}" for c in results[:3]]

    logger.info(
        "[RAG] Search Execution:\n"
        "  Query: %s\n"
        "  Selected document: %s\n"
        "  Selected subject: %s\n"
        "  Candidate documents: %s\n"
        "  Retrieved chunks count: %d\n"
        "  Retrieved document IDs: %s\n"
        "  Top similarity scores: %s\n"
        "  Source pages: %s",
        query_clean,
        target_doc_name or (target_doc_id if target_doc_id else "ALL_DOCUMENTS"),
        subj_norm,
        [d.get("filename") for d in (documents or [])],
        len(results),
        retrieved_ids,
        scores,
        sources
    )

    return results


def get_document_diagnostics(doc_id: str, user_id: str = "user_default") -> Dict[str, Any]:
    """
    Diagnostic helper to report document extraction and vector indexing status.
    """
    processed_path = config.PROCESSED_DIR / f"{doc_id}.json"
    if not processed_path.exists():
        return {"doc_id": doc_id, "status": "NOT_FOUND"}

    with open(processed_path, "r", encoding="utf-8") as f:
        doc_data = json.load(f)

    subject = doc_data.get("subject", config.DEFAULT_SUBJECT)
    v_store = get_subject_vector_store(subject, user_id=user_id)
    matching_vectors = [c for c in v_store.chunks if c.get("doc_id") == doc_id]

    extracted_chars = doc_data.get("extracted_chars", sum(len(c.get("text", "")) for c in doc_data.get("chunks", [])))
    doc_status = doc_data.get("status", "READY" if extracted_chars > 50 else "OCR_REQUIRED")

    return {
        "doc_id": doc_id,
        "filename": doc_data.get("filename"),
        "subject": subject,
        "extracted_chars": extracted_chars,
        "total_units": doc_data.get("total_units", len(doc_data.get("chunks", []))),
        "chunks": len(doc_data.get("chunks", [])),
        "index_vectors": len(matching_vectors),
        "status": doc_status
    }


def format_context_for_prompt(
    chunks: List[Dict[str, Any]],
    active_doc_name: Optional[str] = None,
    active_doc_id: Optional[str] = None
) -> str:
    """
    Format matching document chunks into clean grounded context for LLM prompts.
    Includes explicit ACTIVE DOCUMENT header & strict grounding policy.
    """
    if not chunks:
        return ""

    doc_name = active_doc_name or chunks[0].get("filename") or "Course Material"
    doc_id = active_doc_id or chunks[0].get("doc_id") or "doc_active"

    header_parts = [
        f"CURRENT ACTIVE DOCUMENT: {doc_name}",
        f"DOCUMENT ID: {doc_id}",
        "STRICT GROUNDING RULE: Answer using ONLY the current active document context below. Do NOT use information from a previous or different document.",
        ""
    ]

    context_parts = ["\n".join(header_parts)]
    for idx, chunk in enumerate(chunks, 1):
        filename = chunk.get("doc_name") or chunk.get("filename", doc_name)
        unit_label = chunk.get("unit_label", "Page 1")
        source_ref = f"{filename} — {unit_label}"
        context_parts.append(
            f"--- SOURCE {idx}: [{source_ref}] ---\n{chunk['text']}\n"
        )

    return "\n".join(context_parts)
