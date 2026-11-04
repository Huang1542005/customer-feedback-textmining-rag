"""Unit tests for the customer_feedback.rag package."""

import pytest
import pandas as pd
from pathlib import Path

from customer_feedback.rag.document_loader import (
    Document,
    load_reviews_as_documents,
    load_policy_documents,
)
from customer_feedback.rag.chunking import chunk_document, chunk_documents, split_text_into_chunks
from customer_feedback.rag.embeddings import BaseEmbedder
from customer_feedback.rag.vector_store import ChromaVectorStore
from customer_feedback.rag.retrieval import HybridRetriever
from customer_feedback.rag.answer_generation import RAGGenerator, RetrievedContext


class MockEmbedder(BaseEmbedder):
    """Deterministic dummy embedder for unit testing."""

    @property
    def dimension(self) -> int:
        return 4

    def embed_documents(self, texts):
        results = []
        for text in texts:
            # High weight on 1st dim if "torn" is present
            t = text.lower()
            results.append([1.0 if "torn" in t else 0.0, 0.5, 0.2, 0.1])
        return results

    def embed_query(self, text):
        t = text.lower()
        return [1.0 if "torn" in t else 0.0, 0.5, 0.2, 0.1]


def test_chunking_short_and_long_texts():
    # Short text: should not be split
    short_doc = Document(doc_id="doc1", text="This is a short review.", metadata={"score": 5})
    chunks = chunk_document(short_doc, max_words=10)
    assert len(chunks) == 1
    assert chunks[0].doc_id == "doc1"
    assert chunks[0].metadata["total_chunks"] == 1

    # Long text: should be split with overlap
    long_text = " ".join([f"word_{i}" for i in range(25)])
    long_doc = Document(doc_id="doc2", text=long_text, metadata={"score": 1})
    chunks = chunk_document(long_doc, max_words=10, overlap_words=2)
    assert len(chunks) >= 3
    assert chunks[0].doc_id == "doc2_c1"
    assert chunks[0].metadata["parent_doc_id"] == "doc2"
    assert chunks[0].metadata["chunk_index"] == 0


def test_load_reviews_handles_nan_and_metadata(tmp_path):
    parquet_path = tmp_path / "test_reviews.parquet"
    df = pd.DataFrame(
        [
            {
                "review_id": 101,
                "review_text": "Great packaging and fast shipping.",
                "product_id": "P01",
                "score": 5,
                "is_negative": False,
                "review_date": pd.Timestamp("2026-01-15"),
                "helpful_yes": 3,
                "helpful_total": 4,
                "helpful_ratio": 0.75,
            },
            {
                "review_id": 102,
                "review_text": "Box arrived crushed and leaking.",
                "product_id": "P02",
                "score": 1,
                "is_negative": True,
                "review_date": pd.NaT,
                "helpful_yes": 0,
                "helpful_total": 0,
                "helpful_ratio": float("nan"),  # Must not crash Chroma
            },
        ]
    )
    df.to_parquet(parquet_path)

    docs = load_reviews_as_documents(parquet_path)
    assert len(docs) == 2
    assert docs[0].doc_id == "rev_101"
    assert docs[0].metadata["review_date"] == "2026-01-15"
    assert "helpful_ratio" not in docs[1].metadata  # NaN excluded cleanly


def test_vector_store_and_hybrid_retrieval(tmp_path):
    db_path = tmp_path / "chroma_test"
    embedder = MockEmbedder()
    store = ChromaVectorStore(persist_dir=db_path, embedder=embedder)

    docs = [
        Document(doc_id="r1", text="The bag was completely torn and spilled everywhere.", metadata={"score": 1}),
        Document(doc_id="r2", text="Delicious sweet tea with peach flavor.", metadata={"score": 5}),
        Document(doc_id="r3", text="Terrible bitter taste and stale expired crackers.", metadata={"score": 1}),
    ]

    added = store.add_documents(docs, collection_name="test_collection")
    assert added == 3
    assert store.count("test_collection") == 3

    # Test HybridRetriever
    retriever = HybridRetriever(vector_store=store, corpus_documents=docs)
    results = retriever.hybrid_search("torn bag spilled", collection_name="test_collection", top_k=2)
    assert len(results) >= 1
    # First result should be the torn bag document due to BM25 + dense match
    assert results[0].doc_id == "r1"


def test_offline_rag_generation():
    issue = {
        "issue_id": 1,
        "rank": 1,
        "label": "crushed_box_leakage",
        "top_terms": ["crushed", "box", "broken", "leaking"],
        "priority_score": 88.5,
        "metrics": {"n_reviews": 50, "pct_one_star": 0.90},
    }

    evidence = [
        Document(doc_id="rev_1", text="Box arrived leaking oil.", metadata={"review_id": 1001, "score": 1})
    ]
    policy = [
        Document(
            doc_id="pol_1",
            text="Edge crush test packaging mandatory.",
            metadata={"policy_id": "POL-PKG-001", "title": "Packaging Standards"},
        )
    ]

    ctx = RetrievedContext(
        issue_id=1,
        label="crushed_box_leakage",
        query_str="crushed box broken",
        evidence_reviews=evidence,
        relevant_policies=policy,
    )

    generator = RAGGenerator()
    insight = generator.generate_insight(issue, ctx)

    assert insight.rank == 1
    assert "Packaging" in insight.root_cause
    assert len(insight.citations) >= 2
    assert any("Review #1001" in c.get("id", "") for c in insight.citations)
