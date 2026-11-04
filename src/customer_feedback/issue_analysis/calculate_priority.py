"""Rank detected issues by priority and package them for the RAG / reporting steps.

Priority score (0-100) = weighted sum of four components, each scaled to 0-1:

    volume       share of all complaints in the issue            (min-max across issues)
    severity     share of 1-star reviews inside the issue        (min-max across issues)
    helpfulness  average helpful votes per review                (min-max across issues)
    trend        growth of the issue's share, last N months vs the N months before.
                 Absolute scale: growth <= 0 scores 0, +100% or more scores 1. Only
                 a genuinely growing issue gains priority; a flat one does not.

Weights are a judgement call, not ground truth. Keep them in one place
(DEFAULT_WEIGHTS) and report them next to the ranking. The number of distinct
products is reported (n_products, top_product_share) but not scored, because it
mostly mirrors volume.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_WEIGHTS = {"volume": 0.45, "severity": 0.25, "trend": 0.20, "helpfulness": 0.10}


def summarize_issues(
    reviews: pd.DataFrame, assignments: pd.DataFrame, recent_months: int = 12
) -> pd.DataFrame:
    """Per-issue statistics.

    Args:
        reviews: preprocessed reviews (review_id, score, product_id, helpful_yes, review_date).
        assignments: output of detect_issues (review_id, issue_id, issue_strength).
        recent_months: size of the "recent" and "previous" windows used for the trend.
    """
    data = reviews.merge(assignments, on="review_id")
    data = data[data["issue_id"] >= 0]

    end = data["review_date"].max()
    recent_start = end - pd.DateOffset(months=recent_months)
    prev_start = recent_start - pd.DateOffset(months=recent_months)
    in_recent = data["review_date"] > recent_start
    in_prev = (data["review_date"] > prev_start) & ~in_recent
    total_recent, total_prev = max(int(in_recent.sum()), 1), max(int(in_prev.sum()), 1)

    g = data.groupby("issue_id")
    out = pd.DataFrame(
        {
            "n_reviews": g.size(),
            "pct_one_star": g["score"].apply(lambda s: (s == 1).mean()),
            "avg_score": g["score"].mean(),
            "avg_helpful_votes": g["helpful_yes"].mean(),
            "n_products": g["product_id"].nunique(),
            "top_product_share": g["product_id"].apply(lambda s: s.value_counts(normalize=True).iloc[0]),
            "n_recent": data[in_recent].groupby("issue_id").size(),
            "n_prev": data[in_prev].groupby("issue_id").size(),
        }
    ).fillna(0)
    out["share"] = out["n_reviews"] / out["n_reviews"].sum()

    eps = 1e-3  # smoothing so tiny windows do not explode the ratio
    share_recent = out["n_recent"] / total_recent
    share_prev = out["n_prev"] / total_prev
    out["growth"] = (share_recent + eps) / (share_prev + eps) - 1
    return out.reset_index()


def _minmax(s: pd.Series) -> pd.Series:
    rng = s.max() - s.min()
    return (s - s.min()) / rng if rng > 0 else pd.Series(0.0, index=s.index)


def calculate_priority(summary: pd.DataFrame, weights: dict[str, float] | None = None) -> pd.DataFrame:
    """Add component scores, `priority_score` (0-100) and `rank` (1 = most urgent)."""
    weights = weights or DEFAULT_WEIGHTS
    unknown = set(weights) - set(DEFAULT_WEIGHTS)
    if unknown:
        raise ValueError(f"Unknown weight keys: {sorted(unknown)}")
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("Weights must sum to a positive number.")

    out = summary.copy()
    out["volume"] = _minmax(out["share"])
    out["severity"] = _minmax(out["pct_one_star"])
    out["trend"] = out["growth"].clip(0.0, 1.0)
    out["helpfulness"] = _minmax(out["avg_helpful_votes"])

    out["priority_score"] = 100 * sum(w / total * out[k] for k, w in weights.items())
    out = out.sort_values("priority_score", ascending=False).reset_index(drop=True)
    out["rank"] = np.arange(1, len(out) + 1)
    return out


def representative_reviews(
    reviews: pd.DataFrame, assignments: pd.DataFrame, issue_id: int, top_terms: list[str],
    n: int = 3, min_words: int = 20, max_words: int = 120,
) -> list[dict]:
    """Pick readable example reviews for an issue.

    Ranking: (1) how many DIFFERENT top terms of the issue the review contains, so a
    review mentioning "box", "broken" and "opened" beats one that only says "a box";
    (2) issue_strength; (3) helpful votes. Very short/long reviews are skipped.
    """
    data = reviews.merge(assignments, on="review_id")
    data = data[(data["issue_id"] == issue_id) & data["word_count"].between(min_words, max_words)].copy()
    padded = " " + data["text_normalized"].fillna("") + " "
    data["n_terms"] = sum(padded.str.contains(f" {t} ", regex=False).astype(int) for t in top_terms)
    data = data.sort_values(["n_terms", "issue_strength", "helpful_yes"], ascending=False).head(n)
    return [
        {"review_id": int(r.review_id), "product_id": str(r.product_id),
         "score": int(r.score), "text": str(r.review_text)}
        for r in data.itertuples()
    ]


def build_issue_report(
    reviews: pd.DataFrame, assignments: pd.DataFrame, issues: pd.DataFrame,
    weights: dict[str, float] | None = None, n_examples: int = 3, recent_months: int = 12,
) -> list[dict]:
    """Ranked issues as JSON-ready records (the hand-off format for RAG and reporting)."""
    ranked = calculate_priority(summarize_issues(reviews, assignments, recent_months), weights)
    ranked = ranked.merge(issues, on="issue_id")

    records = []
    for r in ranked.itertuples():
        records.append(
            {
                "rank": int(r.rank),
                "issue_id": int(r.issue_id),
                "label": r.label,
                "top_terms": list(r.top_terms),
                "priority_score": round(float(r.priority_score), 1),
                "metrics": {
                    "n_reviews": int(r.n_reviews),
                    "share_of_complaints": round(float(r.share), 4),
                    "pct_one_star": round(float(r.pct_one_star), 3),
                    "avg_score": round(float(r.avg_score), 2),
                    "avg_helpful_votes": round(float(r.avg_helpful_votes), 2),
                    "n_products": int(r.n_products),
                    "top_product_share": round(float(r.top_product_share), 3),
                    "growth_recent_vs_prev": round(float(r.growth), 3),
                },
                "components": {k: round(float(getattr(r, k)), 3) for k in DEFAULT_WEIGHTS},
                "examples": representative_reviews(
                    reviews, assignments, int(r.issue_id), list(r.top_terms), n_examples
                ),
            }
        )
    return records