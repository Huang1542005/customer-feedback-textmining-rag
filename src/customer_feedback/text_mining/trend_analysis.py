
"""Analyze monthly trends of detected customer issues."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]


def analyze_trends(
    reviews: pd.DataFrame,
    assignments: pd.DataFrame,
    window: int = 3,
    min_count: int = 10,
):
    """Analyze issue shares and growth across monthly windows."""

    required_reviews = {"review_id", "score", "review_date"}
    required_assignments = {"review_id", "issue_id"}

    if not required_reviews.issubset(reviews.columns):
        raise ValueError("Reviews missing required columns")

    if not required_assignments.issubset(assignments.columns):
        raise ValueError("Assignments missing required columns")

    if window < 1 or min_count < 1:
        raise ValueError("window and min_count must be positive")

    if reviews["review_id"].duplicated().any():
        raise ValueError("Duplicate review_id in reviews")

    if assignments["review_id"].duplicated().any():
        raise ValueError("Duplicate review_id in assignments")

    # 1. Keep negative reviews.
    negative = reviews.loc[
        reviews["score"].le(2),
        ["review_id", "review_date"],
    ].copy()

    negative["review_date"] = pd.to_datetime(
        negative["review_date"],
        errors="coerce",
    )
    negative = negative.dropna(subset=["review_date"])

    if negative.empty:
        raise ValueError("No dated negative reviews found")

    negative["month"] = (
        negative["review_date"].dt.to_period("M")
    )

    months = pd.period_range(
        negative["month"].min(),
        negative["month"].max(),
        freq="M",
    )

    # Denominator includes all negative reviews,
    # including ones not assigned to any issue.
    totals = (
        negative.groupby("month")
        .size()
        .reindex(months, fill_value=0)
    )

    # 2. Match each review with its detected issue.
    linked = negative.merge(
        assignments[["review_id", "issue_id"]],
        on="review_id",
        how="left",
        validate="one_to_one",
    )

    linked["issue_id"] = pd.to_numeric(
        linked["issue_id"],
        errors="coerce",
    )
    linked = linked.loc[
        linked["issue_id"].notna()
        & linked["issue_id"].ge(0)
    ].copy()

    if linked.empty:
        raise ValueError("No assigned issues found")

    linked["issue_id"] = linked["issue_id"].astype(int)

    # 3. Count issues by calendar month.
    issue_ids = sorted(linked["issue_id"].unique())

    complete_index = pd.MultiIndex.from_product(
        [issue_ids, months],
        names=["issue_id", "month"],
    )

    monthly = (
        linked.groupby(["issue_id", "month"])
        .size()
        .reindex(complete_index, fill_value=0)
        .rename("issue_count")
        .reset_index()
    )

    monthly["total_negative_count"] = (
        monthly["month"].map(totals).astype(int)
    )

    monthly["monthly_share"] = (
        monthly["issue_count"]
        / monthly["total_negative_count"].replace(0, np.nan)
    )

    # 4. Calculate rolling window counts and shares.
    grouped = monthly.groupby("issue_id")

    monthly["recent_issue_count"] = grouped[
        "issue_count"
    ].transform(
        lambda s: s.rolling(
            window, min_periods=window
        ).sum()
    )

    monthly["recent_total_negative"] = grouped[
        "total_negative_count"
    ].transform(
        lambda s: s.rolling(
            window, min_periods=window
        ).sum()
    )

    monthly["recent_share"] = (
        monthly["recent_issue_count"]
        / monthly["recent_total_negative"].replace(0, np.nan)
    )

    # Previous non-overlapping window of the same length.
    monthly["previous_issue_count"] = (
        monthly.groupby("issue_id")["recent_issue_count"]
        .shift(window)
    )

    monthly["previous_total_negative"] = (
        monthly.groupby("issue_id")["recent_total_negative"]
        .shift(window)
    )

    monthly["previous_share"] = (
        monthly.groupby("issue_id")["recent_share"]
        .shift(window)
    )

    # 5. Growth is undefined if the previous share is zero.
    monthly["growth_rate"] = (
        monthly["recent_share"]
        / monthly["previous_share"].replace(0, np.nan)
        - 1
    )

    # 6. Classify trends.
    def classify(row):
        if (
            pd.isna(row["recent_share"])
            or pd.isna(row["previous_share"])
            or pd.isna(row["previous_total_negative"])
        ):
            return "insufficient_history"

        if (
            row["previous_issue_count"] == 0
            and row["recent_issue_count"] >= min_count
        ):
            return "new_or_emerging"

        if (
            row["previous_issue_count"] < min_count
            or row["recent_issue_count"] < min_count
        ):
            return "low_volume"

        growth = row["growth_rate"]

        if pd.isna(growth):
            return "insufficient_data"

        if growth >= 0.20:
            return "increasing"

        if growth <= -0.20:
            return "decreasing"

        return "stable"

    monthly["trend_status"] = monthly.apply(
        classify, axis=1
    )

    # 7. Latest period for each issue.
    latest = (
        monthly.groupby("issue_id", sort=False)
        .tail(1)
        .copy()
    )

    latest = latest.sort_values(
        ["recent_share", "recent_issue_count"],
        ascending=[False, False],
        na_position="last",
    ).reset_index(drop=True)

    monthly["month"] = monthly["month"].astype(str)
    latest["month"] = latest["month"].astype(str)

    return monthly, latest


def main():
    parser = argparse.ArgumentParser(
        description="Analyze customer issue trends"
    )

    parser.add_argument(
        "--reviews",
        default=str(ROOT / "data/processed/reviews_clean.parquet"),
    )
    parser.add_argument(
        "--assignments",
        default=str(ROOT / "data/processed/issue_assignments.parquet"),
    )
    parser.add_argument(
        "--outdir",
        default=str(ROOT / "data/processed"),
    )
    parser.add_argument("--window", type=int, default=3)
    parser.add_argument("--min-count", type=int, default=10)

    args = parser.parse_args()

    reviews = pd.read_parquet(args.reviews)
    assignments = pd.read_parquet(args.assignments)

    monthly, latest = analyze_trends(
        reviews,
        assignments,
        window=args.window,
        min_count=args.min_count,
    )

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    monthly.to_csv(
        outdir / "issue_monthly_trends.csv",
        index=False,
    )

    latest.to_csv(
        outdir / "issue_trend_summary.csv",
        index=False,
    )

    print("\nLATEST ISSUE TRENDS")
    print(
        latest[
            [
                "issue_id",
                "month",
                "recent_issue_count",
                "recent_share",
                "growth_rate",
                "trend_status",
            ]
        ].round(4).to_string(index=False)
    )

    print(f"\nResults saved to: {outdir}")


if __name__ == "__main__":
    main()
