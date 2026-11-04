"""Resolve evidence identifiers and quotations against supplied output files."""
from __future__ import annotations

import re


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().casefold()


def make_citation(doc: dict, reviews: dict[str, dict]) -> dict:
    metadata = doc.get("metadata") or {}
    kind = doc.get("type") or metadata.get("source", "review")
    if kind == "review":
        raw_id = doc.get("review_id", metadata.get("review_id", doc.get("id", doc.get("doc_id", ""))))
        review_id = re.sub(r"^(?:Review\s*#|rev_)", "", str(raw_id), flags=re.I).split("_c")[0]
        source = reviews.get(review_id)
        quote = str(doc.get("text") or doc.get("snippet") or doc.get("source") or "").strip()
        full_text = str((source or {}).get("review_text") or (source or {}).get("text") or "")
        if not quote:
            quote = full_text
        # Branch output uses trailing ellipses for truncated snippets.
        quote = quote.removesuffix("...").removesuffix("…").strip()
        valid = bool(source and quote and normalize_text(quote) in normalize_text(full_text))
        return {"id": f"Review #{review_id}", "type": "review", "review_id": review_id,
                "quote": quote, "score": (source or {}).get("score"),
                "source_file": "reviews", "verified": valid,
                "reason": "quote_matches_review" if valid else "review_or_quote_not_resolved"}
    policy_id = str(doc.get("policy_id") or metadata.get("policy_id") or doc.get("id") or "")
    text = str(doc.get("text") or "").strip()
    file_name = str(metadata.get("file_name") or doc.get("file_name") or "")
    # A title alone in rag_insights.json does not establish policy evidence.
    valid = bool(policy_id and text and file_name)
    section_id = str(doc.get("doc_id") or "")
    citation_id = f"{policy_id}::{section_id}" if section_id else policy_id
    return {"id": citation_id, "policy_id": policy_id, "type": kind, "quote": text,
            "title": metadata.get("title", doc.get("title", "")),
            "section": metadata.get("section_title", ""), "source_file": file_name,
            "verified": valid,
            "reason": "text_and_source_in_retrieval_output" if valid else "missing_source_text_or_file"}


def collect_citations(issue: dict, retrieval: dict, upstream: dict,
                      reviews: dict[str, dict]) -> list[dict]:
    docs = []
    for key in ("evidence_reviews", "relevant_policies", "documents"):
        docs.extend(retrieval.get(key) or [])
    docs.extend(upstream.get("citations") or [])
    # P3 representative reviews are supplied output, not claimed as P4 retrieval.
    for example in issue.get("examples") or []:
        doc = dict(example, type="review")
        doc["origin"] = "p3_example"
        docs.append(doc)
    result, seen = [], set()
    for doc in docs:
        citation = make_citation(doc, reviews)
        citation["origin"] = doc.get("origin", "p4_output")
        identity = (citation["id"], citation["quote"])
        if identity not in seen:
            seen.add(identity)
            result.append(citation)
    return result
