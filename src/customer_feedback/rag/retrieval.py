"""Hybrid Retrieval engine combining Dense Vector Search and BM25 Sparse Search."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Sequence

from rank_bm25 import BM25Okapi

from customer_feedback.rag.document_loader import Document
from customer_feedback.rag.vector_store import ChromaVectorStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievedContext:
    """Retrieved evidence and policy context for a customer issue."""

    issue_id: int
    label: str
    query_str: str
    evidence_reviews: list[Document] = field(default_factory=list)
    relevant_policies: list[Document] = field(default_factory=list)


class HybridRetriever:
    """Combines Dense Vector Retrieval (ChromaDB) and Sparse BM25 Keyword Search."""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        corpus_documents: Sequence[Document] | None = None,
    ):
        self.vector_store = vector_store
        self.corpus_docs = list(corpus_documents) if corpus_documents else []
        self._doc_by_id: dict[str, Document] = {d.doc_id: d for d in self.corpus_docs}

        # Setup BM25 index if corpus documents provided
        if self.corpus_docs:
            tokenized_corpus = [doc.text.lower().split() for doc in self.corpus_docs]
            self.bm25 = BM25Okapi(tokenized_corpus)
        else:
            self.bm25 = None

    def dense_search(
        self,
        query: str,
        collection_name: str = "feedback_reviews",
        top_k: int = 10,
        where: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Perform dense semantic search on the vector store."""
        return self.vector_store.query(
            query_text=query,
            collection_name=collection_name,
            n_results=top_k,
            where=where,
        )

    def bm25_search(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[Document]:
        """Perform sparse keyword search using BM25."""
        if not self.bm25 or not self.corpus_docs:
            return []

        tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results: list[Document] = []
        for idx in top_indices:
            if scores[idx] > 0:
                doc = self.corpus_docs[idx]
                meta = dict(doc.metadata)
                meta["bm25_score"] = round(float(scores[idx]), 3)
                results.append(Document(doc_id=doc.doc_id, text=doc.text, metadata=meta))

        return results

    def hybrid_search(
        self,
        query: str,
        collection_name: str = "feedback_reviews",
        top_k: int = 5,
        rrf_k: int = 60,
        where: dict[str, Any] | None = None,
        use_bm25: bool = True,
    ) -> list[Document]:
        """Reciprocal Rank Fusion (RRF) between Dense and Sparse results."""
        dense_results = self.dense_search(query, collection_name=collection_name, top_k=top_k * 2, where=where)
        bm25_results = self.bm25_search(query, top_k=top_k * 2) if (use_bm25 and self.bm25) else []

        if not bm25_results:
            return dense_results[:top_k]

        scores: dict[str, float] = {}
        doc_map: dict[str, Document] = {}

        # Score dense ranks
        for rank, doc in enumerate(dense_results):
            doc_map[doc.doc_id] = doc
            scores[doc.doc_id] = scores.get(doc.doc_id, 0.0) + (1.0 / (rrf_k + rank + 1))

        # Score sparse ranks
        for rank, doc in enumerate(bm25_results):
            if doc.doc_id not in doc_map:
                doc_map[doc.doc_id] = doc
            scores[doc.doc_id] = scores.get(doc.doc_id, 0.0) + (1.0 / (rrf_k + rank + 1))

        sorted_ids = sorted(scores.keys(), key=lambda d_id: scores[d_id], reverse=True)[:top_k]
        final_docs: list[Document] = []

        for d_id in sorted_ids:
            doc = doc_map[d_id]
            doc.metadata["rrf_score"] = round(scores[d_id], 5)
            final_docs.append(doc)

        return final_docs

    def retrieve_context_for_issue(
        self,
        issue: dict[str, Any],
        top_reviews: int = 5,
        top_policies: int = 3,
        reviews_collection: str = "feedback_reviews",
        policies_collection: str = "feedback_policies",
    ) -> RetrievedContext:
        """Retrieve both customer review evidence and relevant policy standards for an issue."""
        label = issue.get("label", "")
        top_terms = issue.get("top_terms", [])
        issue_id = int(issue.get("issue_id", 0))

        # Formulate search query emphasizing defect keywords
        query = f"{label} {' '.join(top_terms)}"

        evidence_reviews = self.hybrid_search(
            query=query,
            collection_name=reviews_collection,
            top_k=top_reviews,
        )

        relevant_policies = self.dense_search(
            query=query,
            collection_name=policies_collection,
            top_k=top_policies,
        )

        return RetrievedContext(
            issue_id=issue_id,
            label=label,
            query_str=query,
            evidence_reviews=evidence_reviews,
            relevant_policies=relevant_policies,
        )
