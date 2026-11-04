"""Read file hand-offs from P1-P4 without importing their implementation."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def read_records(path: Path, columns: list[str] | None = None) -> list[dict[str, Any]]:
    if path.suffix == ".json":
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(value, dict):
            value = value.get("issues", value.get("records", value.get("results")))
        if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
            raise ValueError(f"{path.name}: expected a list of objects")
        return value
    if path.suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))
    if path.suffix == ".parquet":
        import pandas as pd

        # Convert NaN, datetime and numpy scalars to portable JSON values.
        if columns:
            import pyarrow.parquet as pq
            available = pq.read_schema(path).names
            columns = [column for column in columns if column in available]
            if "review_text" in columns and "text" in columns:
                columns.remove("text")
        frame = pd.read_parquet(path, columns=columns)
        return json.loads(frame.to_json(orient="records", date_format="iso"))
    raise ValueError(f"Unsupported artifact: {path.name}")


def number(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    result = float(value)
    if not math.isfinite(result):
        return default
    return result


def identifier(value: Any) -> str:
    if value is None or str(value).strip() == "":
        raise ValueError("Missing record identifier")
    return str(value).strip()


def unique_index(rows: list[dict], key: str) -> dict[str, dict]:
    result = {}
    for row in rows:
        identity = identifier(row.get(key))
        if identity in result:
            raise ValueError(f"Duplicate {key}: {identity}")
        result[identity] = row
    return result


def load_bundle(directory: str | Path) -> dict[str, Any]:
    """Support both the assignment names and actual current branch outputs."""
    directory = Path(directory)
    names = {
        "issues": ("issues.json", "issues_ranked.json"),
        "reviews": ("clean_reviews.parquet", "reviews_clean.parquet", "reviews_clean.csv"),
        "sentiment": ("sentiment.parquet", "sentiment.csv"),
        "clusters": ("clusters.parquet", "issue_assignments.parquet", "issue_assignments.csv"),
        "trends": ("trend.csv", "issue_monthly_trends.csv"),
        "patterns": ("patterns.csv", "issue_trend_summary.csv"),
        "retrieval": ("retrieval_results.json",),
        "upstream_insights": ("rag_insights.json",),
    }
    bundle: dict[str, Any] = {"manifest": [], "warnings": [], "provenance": {}}
    provenance = directory / "provenance.json"
    if provenance.is_file():
        bundle["provenance"] = json.loads(provenance.read_text(encoding="utf-8-sig"))
        bundle["manifest"].append({"kind": "provenance", "file": provenance.name,
                                   "sha256": hashlib.sha256(provenance.read_bytes()).hexdigest(), "rows": 1})
    for kind, candidates in names.items():
        matches = [directory / name for name in candidates if (directory / name).is_file()]
        if len(matches) > 1:
            raise ValueError(f"Ambiguous {kind} inputs: {', '.join(p.name for p in matches)}")
        columns = ["review_id", "review_text", "text", "score", "sentiment", "review_date"] if kind == "reviews" else None
        bundle[kind] = read_records(matches[0], columns=columns) if matches else []
        if matches:
            path = matches[0]
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            bundle["manifest"].append({"kind": kind, "file": path.name,
                                       "sha256": digest.hexdigest(), "rows": len(bundle[kind])})
        elif kind != "upstream_insights":
            bundle["warnings"].append(f"Missing {kind}: expected one of {', '.join(candidates)}")
    if not bundle["issues"]:
        raise ValueError("No issues found. Run P3 first (issues.json or issues_ranked.json).")
    for kind, key in (("issues", "issue_id"), ("reviews", "review_id"),
                      ("sentiment", "review_id"), ("clusters", "review_id"),
                      ("retrieval", "issue_id"), ("upstream_insights", "issue_id")):
        unique_index(bundle[kind], key)
    if bundle["provenance"].get("raw_row_limit"):
        bundle["warnings"].append(f"Partial dataset: first {bundle['provenance']['raw_row_limit']} raw rows only.")
    if bundle["retrieval"]:
        indexed = bundle["retrieval"][0].get("indexed_review_count")
        if indexed is not None and indexed < len(bundle["reviews"]):
            bundle["warnings"].append(f"P4 indexed only the first {indexed} of {len(bundle['reviews'])} cleaned reviews.")
    bundle["warnings"].extend(bundle["provenance"].get("notes", []))
    return bundle
