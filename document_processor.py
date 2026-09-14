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
import faiss

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
# 1. SUBJECT-ISOLATED FAISS VECTOR STORE
# ==============================================================================
class SubjectVectorStore:
    """
    Manages vector embeddings and chunk metadata isolated by Subject using FAISS.
    Guarantees that querying subject 'Java' only retrieves Java materials.
    """

    def __init__(self, subject: str, dimension: int = 768):
        self.subject: str = subject.strip().title()
        self.dimension: int = dimension
        self.sanitized_name: str = re.sub(r"[^\w\-]", "_", self.subject.lower())
        self.index_path: Path = config.INDEXES_DIR / f"{self.sanitized_name}.faiss"
        self.meta_path: Path = config.INDEXES_DIR / f"{self.sanitized_name}_meta.json"

        self.index: Optional[faiss.IndexFlatIP] = None
        self.chunks: List[Dict[str, Any]] = []
        self._load_or_create()

    def _load_or_create(self) -> None:
        """Load existing index from disk or initialize new FAISS IndexFlatIP."""
        if self.index_path.exists() and self.meta_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                logger.info("Loaded vector index for subject '%s' (%d chunks)", self.subject, len(self.chunks))
                return
            except Exception as e:
                logger.warning("Error loading index for subject '%s': %s. Rebuilding.", self.subject, str(e))

        self.index = faiss.IndexFlatIP(self.dimension)
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

        if self.index is None:
            self.index = faiss.IndexFlatIP(matrix.shape[1])

        self.index.add(matrix)
        self.chunks.extend(new_chunks)
        self._save()

    def _save(self) -> None:
        """Persist index and chunk metadata to disk."""
        config.INDEXES_DIR.mkdir(parents=True, exist_ok=True)
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_path))
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2)

    def search(self, query_embedding: List[float], top_k: int = config.TOP_K) -> List[Dict[str, Any]]:
        """Perform semantic search using query vector."""
        if self.index is None or self.index.ntotal == 0 or not self.chunks:
            return []

        q_vec = np.array([query_embedding], dtype="float32")
        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec = q_vec / norm

        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(q_vec, k)

        results = []
        for idx_pos, chunk_idx in enumerate(indices[0]):
            if 0 <= chunk_idx < len(self.chunks):
                chunk = dict(self.chunks[chunk_idx])
                chunk["score"] = float(distances[0][idx_pos])
                results.append(chunk)

        return results


# Cache of loaded vector stores by subject
_VECTOR_STORES: Dict[str, SubjectVectorStore] = {}


def get_subject_vector_store(subject: str) -> SubjectVectorStore:
    """Retrieve or create the subject-isolated vector store."""
    subj_norm = subject.strip().title()
    if subj_norm not in _VECTOR_STORES:
        _VECTOR_STORES[subj_norm] = SubjectVectorStore(subj_norm)
    return _VECTOR_STORES[subj_norm]


# ==============================================================================
# 2. DOCUMENT PARSING & CHUNKING ENGINE
# ==============================================================================
def process_uploaded_file(
    file_bytes: bytes,
    filename: str,
    subject: str = config.DEFAULT_SUBJECT
) -> Dict[str, Any]:
    """
    Parse uploaded PDF, PPT, or PPTX bytes up to MAX_FILE_SIZE_MB.
    Extracts complete text, performs chunking with page/slide metadata,
    generates embeddings, and registers in subject vector index and SQLite DB.
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

    # Save raw file to uploads directory
    saved_file_path = config.UPLOADS_DIR / f"{doc_id}_{filename}"
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

    # Store in subject vector index
    if chunks and embeddings:
        v_store = get_subject_vector_store(subj_norm)
        v_store.add_chunks(chunks, embeddings)

    doc_data = {
        "doc_id": doc_id,
        "filename": filename,
        "file_hash": file_hash,
        "subject": subj_norm,
        "file_size_mb": file_size_mb,
        "file_type": file_ext.upper(),
        "total_units": len(chunks),
        "chunks": chunks
    }

    # Save processed JSON and database record
    processed_path = config.PROCESSED_DIR / f"{doc_id}.json"
    with open(processed_path, "w", encoding="utf-8") as f:
        json.dump(doc_data, f, indent=2)

    database.save_document_record(doc_data, str(saved_file_path))

    logger.info(
        "Processed and indexed %s for subject '%s' (%s MB, %d chunks)",
        filename, subj_norm, file_size_mb, len(chunks)
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
    top_k: int = config.TOP_K
) -> List[Dict[str, Any]]:
    """
    Perform semantic search for query within course materials isolated by subject.
    Returns the top_k matching chunks with full source metadata.
    """
    if not query or not query.strip():
        return []

    subj_norm = subject.strip().title()

    # Query subject vector store first
    v_store = get_subject_vector_store(subj_norm)
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
