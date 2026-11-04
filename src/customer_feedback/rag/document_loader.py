"""Document loading utilities for Customer Feedback RAG.

Loads two core knowledge sources:
1. Customer reviews from `reviews_clean.parquet` (using natural text `review_text`).
2. Domain policy documents from `docs/policies/` (standards, refund, shipping rules).
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REVIEWS_PATH = ROOT / "data/processed/reviews_clean.parquet"
DEFAULT_POLICIES_DIR = ROOT / "docs/policies"
DEFAULT_ISSUES_PATH = ROOT / "data/processed/issues_ranked.json"


@dataclass
class Document:
    """Standard document format for chunking, indexing, and retrieval."""

    doc_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "text": self.text,
            "metadata": self.metadata,
        }


def load_reviews_as_documents(
    path: str | Path = DEFAULT_REVIEWS_PATH,
    only_negative: bool = False,
    max_docs: int | None = None,
) -> list[Document]:
    """Load reviews from cleaned parquet as Document objects.

    Follows rules from data_schema.pdf:
    - Uses `review_text` for natural language embedding/LLM context.
    - Sanitizes metadata: casts `review_date` to ISO string, omits NaN values
      to ensure ChromaDB compatibility.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Review parquet file not found at: {path}")

    logger.info("Loading reviews from %s ...", path)
    df = pd.read_parquet(path)

    if only_negative and "is_negative" in df.columns:
        df = df[df["is_negative"]].copy()

    if max_docs is not None and len(df) > max_docs:
        df = df.head(max_docs).copy()

    documents: list[Document] = []
    for row in df.itertuples():
        text = str(getattr(row, "review_text", "")).strip()
        if not text:
            continue

        review_id = int(getattr(row, "review_id"))
        metadata: dict[str, Any] = {
            "doc_id": f"rev_{review_id}",
            "review_id": review_id,
            "source": "review",
            "product_id": str(getattr(row, "product_id", "")),
            "score": int(getattr(row, "score", 0)),
            "is_negative": bool(getattr(row, "is_negative", False)),
        }

        # Date conversion (Chroma cannot store datetime objects)
        review_date = getattr(row, "review_date", None)
        if pd.notna(review_date):
            metadata["review_date"] = str(pd.to_datetime(review_date).strftime("%Y-%m-%d"))

        # Helpfulness metrics (handle NaNs cleanly)
        if hasattr(row, "helpful_yes") and pd.notna(row.helpful_yes):
            metadata["helpful_yes"] = int(row.helpful_yes)
        if hasattr(row, "helpful_total") and pd.notna(row.helpful_total):
            metadata["helpful_total"] = int(row.helpful_total)
        if hasattr(row, "helpful_ratio") and pd.notna(row.helpful_ratio):
            metadata["helpful_ratio"] = round(float(row.helpful_ratio), 3)

        documents.append(
            Document(
                doc_id=f"rev_{review_id}",
                text=text,
                metadata=metadata,
            )
        )

    logger.info("Loaded %d review documents.", len(documents))
    return documents


def load_policy_documents(
    policy_dir: str | Path = DEFAULT_POLICIES_DIR,
) -> list[Document]:
    """Load policy markdown files and split into section-level Documents."""
    policy_dir = Path(policy_dir)
    if not policy_dir.exists():
        logger.warning("Policy directory %s does not exist.", policy_dir)
        return []

    documents: list[Document] = []
    header_pattern = re.compile(r"^(#{1,3})\s+(.+)$", flags=re.MULTILINE)

    for md_file in sorted(policy_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        title_match = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
        doc_title = title_match.group(1).strip() if title_match else md_file.stem.replace("_", " ").title()

        doc_id_match = re.search(r"\*\*Document ID:\*\*\s*([^\n\r]+)", content)
        doc_code = doc_id_match.group(1).strip() if doc_id_match else md_file.stem

        # Split by section headers (## or ###)
        sections = re.split(r"\n(?=##\s+)", content)
        for idx, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue

            sec_header_match = header_pattern.search(section)
            sec_title = sec_header_match.group(2).strip() if sec_header_match else f"Section {idx+1}"

            section_doc_id = f"pol_{doc_code}_{idx+1}"
            documents.append(
                Document(
                    doc_id=section_doc_id,
                    text=f"[{doc_title} - {sec_title}]\n{section}",
                    metadata={
                        "doc_id": section_doc_id,
                        "source": "policy",
                        "policy_id": doc_code,
                        "title": doc_title,
                        "section_title": sec_title,
                        "file_name": md_file.name,
                    },
                )
            )

    logger.info("Loaded %d policy documents from %s.", len(documents), policy_dir)
    return documents


def load_ranked_issues(
    path: str | Path = DEFAULT_ISSUES_PATH,
) -> list[dict[str, Any]]:
    """Load detected and prioritized issues from JSON output."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Ranked issues file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

