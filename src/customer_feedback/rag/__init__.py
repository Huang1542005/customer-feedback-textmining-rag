"""Customer Feedback RAG package.

Provides document loading, chunking, vector embedding, hybrid retrieval,
and evidence-based answer generation.
"""

from customer_feedback.rag.answer_generation import IssueInsight, RAGGenerator
from customer_feedback.rag.chunking import chunk_documents
from customer_feedback.rag.document_loader import (
    Document,
    load_policy_documents,
    load_ranked_issues,
    load_reviews_as_documents,
)
from customer_feedback.rag.embeddings import BaseEmbedder, get_embedder
from customer_feedback.rag.retrieval import HybridRetriever, RetrievedContext
from customer_feedback.rag.vector_store import ChromaVectorStore

__all__ = [
    "Document",
    "load_reviews_as_documents",
    "load_policy_documents",
    "load_ranked_issues",
    "chunk_documents",
    "BaseEmbedder",
    "get_embedder",
    "ChromaVectorStore",
    "HybridRetriever",
    "RetrievedContext",
    "RAGGenerator",
    "IssueInsight",
]

