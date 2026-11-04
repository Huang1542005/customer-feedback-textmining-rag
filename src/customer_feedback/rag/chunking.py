"""Text chunking utilities for customer reviews and policy documents.

Handles length constraints (16.6% of reviews > 128 words) to ensure
embeddings and retrieval do not truncate critical customer context.
"""
from __future__ import annotations

import logging
import re
from typing import Sequence

from customer_feedback.rag.document_loader import Document

logger = logging.getLogger(__name__)


def split_text_into_chunks(
    text: str,
    max_words: int = 120,
    overlap_words: int = 20,
) -> list[str]:
    """Split a string into overlapping chunks based on word boundaries."""
    text = text.strip()
    if not text:
        return []

    words = text.split()
    if len(words) <= max_words:
        return [text]

    chunks: list[str] = []
    step = max(1, max_words - overlap_words)

    for i in range(0, len(words), step):
        chunk_words = words[i : i + max_words]
        if not chunk_words:
            break
        chunk_str = " ".join(chunk_words)
        chunks.append(chunk_str)
        if i + max_words >= len(words):
            break

    return chunks


def chunk_document(
    doc: Document,
    max_words: int = 120,
    overlap_words: int = 20,
) -> list[Document]:
    """Chunk a single Document into sub-documents if it exceeds max_words."""
    text_chunks = split_text_into_chunks(doc.text, max_words=max_words, overlap_words=overlap_words)

    if len(text_chunks) <= 1:
        doc.metadata["chunk_index"] = 0
        doc.metadata["total_chunks"] = 1
        doc.metadata["parent_doc_id"] = doc.doc_id
        return [doc]

    sub_docs: list[Document] = []
    total = len(text_chunks)

    for idx, chunk_text in enumerate(text_chunks):
        chunk_meta = dict(doc.metadata)
        chunk_meta["chunk_index"] = idx
        chunk_meta["total_chunks"] = total
        chunk_meta["parent_doc_id"] = doc.doc_id

        sub_docs.append(
            Document(
                doc_id=f"{doc.doc_id}_c{idx+1}",
                text=chunk_text,
                metadata=chunk_meta,
            )
        )

    return sub_docs


def chunk_documents(
    documents: Sequence[Document],
    max_words: int = 120,
    overlap_words: int = 20,
) -> list[Document]:
    """Process a list of documents and return all chunked sub-documents."""
    all_chunks: list[Document] = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc, max_words=max_words, overlap_words=overlap_words))

    logger.info("Chunked %d original documents into %d chunks.", len(documents), len(all_chunks))
    return all_chunks

