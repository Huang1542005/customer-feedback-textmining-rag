"""Run issue analysis: detect issue groups in complaints -> rank them -> save.

Outputs (in --outdir):
    issue_assignments.parquet   review_id, issue_id, issue_strength   (per complaint)
    issues_ranked.json          ranked issues with metrics + example reviews (for RAG / reporting)
    issues_ranked.csv           same ranking as a flat table (for quick looks / slides)

Examples:
    python scripts/run_issue_analysis.py
    python scripts/run_issue_analysis.py --n-issues 15 --method kmeans
    python scripts/run_issue_analysis.py --compare
"""
import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from customer_feedback.issue_analysis.calculate_priority import build_issue_report  # noqa: E402
from customer_feedback.issue_analysis.detect_issues import (  # noqa: E402
    IssueConfig, detect_issues, evaluate_issues,
)


def main() -> None:
    p = argparse.ArgumentParser(description="Detect and rank customer issues")
    p.add_argument("--input", default=str(ROOT / "data/processed/reviews_clean.parquet"))
    p.add_argument("--outdir", default=str(ROOT / "data/processed"))
    p.add_argument("--n-issues", type=int, default=12)
    p.add_argument("--method", choices=["nmf", "kmeans"], default="nmf")
    p.add_argument("--compare", action="store_true", help="Compare NMF and KMeans, then exit")
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    df = pd.read_parquet(args.input)

    if args.compare:
        rows = []
        for method in ("nmf", "kmeans"):
            res = detect_issues(df, IssueConfig(n_issues=args.n_issues, method=method))
            rows.append(evaluate_issues(res))
        print("\n" + pd.DataFrame(rows).to_string(index=False) + "\n")
        return

    cfg = IssueConfig(n_issues=args.n_issues, method=args.method)
    result = detect_issues(df, cfg)
    print("\nQuality:", evaluate_issues(result))

    report = build_issue_report(df, result.assignments, result.issues)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    result.assignments.to_parquet(outdir / "issue_assignments.parquet", index=False)
    (outdir / "issues_ranked.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    flat = pd.DataFrame(
        [{"rank": r["rank"], "issue_id": r["issue_id"], "label": r["label"],
          "priority_score": r["priority_score"], **r["metrics"]} for r in report]
    )
    flat.to_csv(outdir / "issues_ranked.csv", index=False)

    print("\nRanked issues")
    print(flat[["rank", "issue_id", "label", "priority_score", "n_reviews",
                "pct_one_star", "growth_recent_vs_prev"]].to_string(index=False))
    print(f"\nSaved to {outdir}\n")


if __name__ == "__main__":
    main()