"""P5 execution adapter: invoke unchanged P4 APIs and serialize their retrieval output.

This bypasses the broken upstream CLI entry point without changing its source.
It does not implement or replace retrieval algorithms.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--upstream-root", type=Path, required=True)
    p.add_argument("--input-dir", type=Path, required=True)
    p.add_argument("--max-reviews", type=int, default=1000)
    p.add_argument("--provider", choices=("local", "gemini"), default="local")
    args = p.parse_args()
    if args.max_reviews < 1:
        p.error("--max-reviews must be positive")
    sys.path.insert(0, str(args.upstream_root / "src"))
    from customer_feedback.rag.chunking import chunk_documents
    from customer_feedback.rag.document_loader import load_policy_documents, load_ranked_issues, load_reviews_as_documents
    from customer_feedback.rag.embeddings import get_embedder
    from customer_feedback.rag.retrieval import HybridRetriever
    from customer_feedback.rag.vector_store import ChromaVectorStore

    reviews = load_reviews_as_documents(args.input_dir / "reviews_clean.parquet", max_docs=args.max_reviews)
    policies = load_policy_documents(args.upstream_root / "docs/policies")
    review_chunks = chunk_documents(reviews, max_words=120, overlap_words=20)
    policy_chunks = chunk_documents(policies, max_words=200, overlap_words=30)
    store = ChromaVectorStore(persist_dir=args.input_dir / "vector_store", embedder=get_embedder(args.provider))
    review_collection = f"p5_reviews_{args.provider}"
    policy_collection = f"p5_policies_{args.provider}"
    store.add_documents(review_chunks, collection_name=review_collection)
    store.add_documents(policy_chunks, collection_name=policy_collection)
    retriever = HybridRetriever(vector_store=store, corpus_documents=review_chunks)
    records = []
    for issue in load_ranked_issues(args.input_dir / "issues_ranked.json"):
        context = retriever.retrieve_context_for_issue(issue, top_reviews=4, top_policies=2,
                                                      reviews_collection=review_collection,
                                                      policies_collection=policy_collection)
        records.append({"issue_id": context.issue_id, "query": context.query_str,
                        "indexed_review_count": len(reviews), "indexed_policy_sections": len(policies),
                        "evidence_reviews": [doc.to_dict() for doc in context.evidence_reviews],
                        "relevant_policies": [doc.to_dict() for doc in context.relevant_policies]})
    (args.input_dir / "retrieval_results.json").write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Exported P4 evidence for {len(records)} issues ({len(reviews)} indexed reviews)")


if __name__ == "__main__":
    main()
