"""CLI pipeline for Customer Feedback RAG.

Indexes customer reviews and operational policies into a Vector Store,
retrieves evidence for prioritized issues, and generates an executive report with citations.

Usage:
    python scripts/run_rag.py
    python scripts/run_rag.py --max-reviews 500
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

load_dotenv()

from customer_feedback.rag.answer_generation import RAGGenerator  # noqa: E402
from customer_feedback.rag.chunking import chunk_documents  # noqa: E402
from customer_feedback.rag.document_loader import (  # noqa: E402
    load_policy_documents,
    load_ranked_issues,
    load_reviews_as_documents,
)
from customer_feedback.rag.embeddings import get_embedder  # noqa: E402
from customer_feedback.rag.retrieval import HybridRetriever  # noqa: E402
from customer_feedback.rag.vector_store import ChromaVectorStore  # noqa: E402


def build_markdown_report(insights: list[dict], issues: list[dict]) -> str:
    """Format RAG insights into an executive markdown report."""
    lines = [
        "# Customer Feedback RAG Analysis Report",
        "",
        "## Executive Summary",
        "This report synthesizes text mining issue detection with Retrieval-Augmented Generation (RAG). "
        "For each top customer complaint cluster, the system retrieved relevant empirical reviews and internal "
        "operating policies to diagnose root causes and propose compliant corrective actions.",
        "",
        "---",
        "",
    ]

    for item in insights:
        lines.append(f"### Rank #{item['rank']}: {item['label'].upper()}")
        lines.append(f"- **Priority Score:** {item['priority_score']:.1f}/100")
        lines.append("")
        lines.append("#### 1. Root Cause Analysis")
        lines.append(item["root_cause"])
        lines.append("")
        lines.append("#### 2. Impact Assessment")
        lines.append(item["impact_assessment"])
        lines.append("")
        lines.append("#### 3. Actionable Recommendations")
        for rec in item["recommendations"]:
            lines.append(f"- {rec}")
        lines.append("")
        lines.append("#### 4. Evidence Citations")
        for cite in item["citations"]:
            if cite.get("type") == "review":
                lines.append(f"- **{cite['id']}**: {cite.get('snippet', cite.get('source', ''))}")
            else:
                lines.append(f"- **Policy [{cite['id']}]**: {cite.get('title', cite.get('source', ''))}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAG pipeline on customer feedback and issues")
    parser.add_argument("--issues", default=str(ROOT / "data/processed/issues_ranked.json"))
    parser.add_argument("--reviews", default=str(ROOT / "data/processed/reviews_clean.parquet"))
    parser.add_argument("--policies", default=str(ROOT / "docs/policies"))
    parser.add_argument("--vectordb", default=str(ROOT / "data/vector_store"))
    parser.add_argument("--out-json", default=str(ROOT / "data/processed/rag_insights.json"))
    parser.add_argument("--out-report", default=str(ROOT / "reports/rag_insight_report.md"))
    parser.add_argument("--max-reviews", type=int, default=None, help="Limit number of reviews to index (for fast testing)")
    parser.add_argument("--provider", default="local", choices=["local", "gemini"], help="Embedding & LLM provider")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    # 1. Load documents
    logging.info("Step 1: Loading reviews and policy documents...")
    issues = load_ranked_issues(args.issues)
    reviews_docs = load_reviews_as_documents(args.reviews, max_docs=args.max_reviews)
    policy_docs = load_policy_documents(args.policies)

    # 2. Chunk documents
    logging.info("Step 2: Chunking documents...")
    chunked_reviews = chunk_documents(reviews_docs, max_words=120, overlap_words=20)
    chunked_policies = chunk_documents(policy_docs, max_words=200, overlap_words=30)

    # 3. Setup embeddings and vector store
    logging.info("Step 3: Initializing Embeddings and Chroma Vector Store...")
    embedder = get_embedder(provider=args.provider)
    vector_store = ChromaVectorStore(persist_dir=args.vectordb, embedder=embedder)

    # Index policies
    logging.info("Indexing %d policy sections...", len(chunked_policies))
    vector_store.add_documents(chunked_policies, collection_name="feedback_policies")

    # Index reviews
    logging.info("Indexing %d review chunks...", len(chunked_reviews))
    vector_store.add_documents(chunked_reviews, collection_name="feedback_reviews")

    # 4. Setup Hybrid Retriever
    logging.info("Step 4: Initializing Hybrid Retriever (Dense + BM25)...")
    retriever = HybridRetriever(vector_store=vector_store, corpus_documents=chunked_reviews)

    # 5. Generate Insights
    logging.info("Step 5: Generating evidence-backed insights for ranked issues...")
    generator = RAGGenerator()
    insights = []

    for issue in issues:
        logging.info("Processing Issue #%d: %s (Priority: %.1f)", issue.get("rank", 0), issue.get("label"), issue.get("priority_score", 0))
        ctx = retriever.retrieve_context_for_issue(issue, top_reviews=4, top_policies=2)
        insight = generator.generate_insight(issue, ctx)
        insights.append(insight.to_dict())

    # 6. Save results
    out_json_path = Path(args.out_json)
    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    out_json_path.write_text(json.dumps(insights, indent=2, ensure_ascii=False), encoding="utf-8")
    logging.info("Saved insights JSON to %s", out_json_path)

    out_report_path = Path(args.out_report)
    out_report_path.parent.mkdir(parents=True, exist_ok=True)
    report_content = build_markdown_report(insights, issues)
    out_report_path.write_text(report_content, encoding="utf-8")
    logging.info("Saved executive report to %s", out_report_path)

    print("\n" + "=" * 60)
    print("RAG PIPELINE EXECUTION COMPLETED")
    print(f"- Processed issues: {len(insights)}")
    print(f"- JSON output: {out_json_path}")
    print(f"- Markdown report: {out_report_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

