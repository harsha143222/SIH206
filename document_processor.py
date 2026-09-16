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

    def search(self, query_embedding: List[float], top_k: int = config.TOP_K) -> List[Dict[str, Any]]:
        """Perform semantic search using query vector."""
        if not self.chunks:
            return []

        q_vec = np.array([query_embedding], dtype="float32")
        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec = q_vec / norm

        # 1. Use FAISS if available and loaded
        if FAISS_AVAILABLE and self.index is not None and self.index.ntotal > 0:
            k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(q_vec, k)

            results = []
            for idx_pos, chunk_idx in enumerate(indices[0]):
                if 0 <= chunk_idx < len(self.chunks):
                    chunk = dict(self.chunks[chunk_idx])
                    chunk["score"] = float(distances[0][idx_pos])
                    results.append(chunk)
            return results

        # 2. Fallback to Numpy Cosine Similarity Matrix Search
        if self.embeddings_matrix is not None and len(self.embeddings_matrix) > 0:
            scores = np.dot(self.embeddings_matrix, q_vec.T).flatten()
            k = min(top_k, len(scores))
            top_indices = np.argsort(scores)[::-1][:k]

            results = []
            for idx in top_indices:
                if 0 <= idx < len(self.chunks):
                    chunk = dict(self.chunks[idx])
                    chunk["score"] = float(scores[idx])
                    results.append(chunk)
            return results

        return []


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

    doc_data = {
        "user_id": str(user_id),
        "doc_id": doc_id,
        "filename": filename,
        "file_hash": file_hash,
        "subject": subj_norm,
        "file_size_mb": file_size_mb,
        "file_type": file_ext.upper(),
        "total_units": len(chunks),
        "chunks": chunks,
        "overview": overview
    }

    # Save processed JSON and database record
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
    text = re.sub(r'<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>', '', text, flags=re.IGNORECASE)
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
        main_topics = list(dict.fromkeys([strip_html_tags(c.get("section_title", f"Unit {idx+1}")) for idx, c in enumerate(chunks[:5]) if c.get("section_title")]))
        if not main_topics:
            main_topics = ["Overview of " + clean_fn]
        key_concepts = ["Core Concepts in " + clean_fn]
        recommended_order = [f"{i+1}. {t}" for i, t in enumerate(main_topics)]
        exam_points = ["Review key sections covered in document"]

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
    """Extract text from PDF using pypdf, preserving page metadata."""
    import pypdf

    chunks = []
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            text = (page.extract_text() or "").strip()
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
        logger.error("Error reading PDF %s: %s", filename, str(e))
        raise DocumentProcessingError(f"Failed to parse PDF file '{filename}': {str(e)}") from e

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
    user_id: str = "user_default"
) -> List[Dict[str, Any]]:
    """
    Perform semantic search for query within course materials isolated by subject and user.
    Returns the top_k matching chunks with full source metadata.
    """
    if not query or not query.strip():
        return []

    subj_norm = subject.strip().title()

    # Query subject vector store first
    v_store = get_subject_vector_store(subj_norm, user_id=user_id)
    query_embeddings = gemini_client.generate_embeddings([query])

    if query_embeddings and v_store.chunks:
        results = v_store.search(query_embeddings[0], top_k=top_k)
        if results:
            return results

    # Fallback search over documents passed in memory if vector index is empty
    if documents:
        in_mem_chunks = []
        for doc in documents:
            if doc.get("subject", subj_norm) == subj_norm:
                for c in doc.get("chunks", []):
                    in_mem_chunks.append(c)

        if in_mem_chunks:
            # Keyword / scoring fallback
            words = set(re.findall(r"\w{3,}", query.lower()))
            scored = []
            for c in in_mem_chunks:
                c_text = c.get("text", "").lower()
                matches = sum(1 for w in words if w in c_text)
                if matches > 0:
                    scored.append((matches, c))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [c for _, c in scored[:top_k]]

    return []


def format_context_for_prompt(chunks: List[Dict[str, Any]]) -> str:
    """Format matching document chunks into clean grounded context for LLM prompts."""
    if not chunks:
        return ""

    context_parts = []
    for idx, chunk in enumerate(chunks, 1):
        filename = chunk.get("doc_name") or chunk.get("filename", "Course Material")
        unit_label = chunk.get("unit_label", "Page 1")
        source_ref = f"{filename} — {unit_label}"
        context_parts.append(
            f"--- SOURCE {idx}: [{source_ref}] ---\n{chunk['text']}\n"
        )

    return "\n".join(context_parts)
