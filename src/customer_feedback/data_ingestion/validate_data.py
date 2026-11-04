"""Data-quality checks for review data after loading.

Two severity levels:
- error: schema/logic violations -> offending rows are dropped (drop_invalid=True)
- warning: issues worth knowing about but not handled here (nulls, duplicates, ...) -> left to `preprocessing/`
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

REQUIRED_COLUMNS = [
    "review_id", "product_id", "user_id", "profile_name",
    "helpful_yes", "helpful_total", "score", "timestamp",
    "summary", "text", "review_date",
]


@dataclass
class ValidationReport:
    n_rows_in: int = 0
    n_rows_out: int = 0
    errors: dict[str, int] = field(default_factory=dict)
    warnings: dict[str, int] = field(default_factory=dict)
    stats: dict[str, object] = field(default_factory=dict)

    @property
    def n_dropped(self) -> int:
        return self.n_rows_in - self.n_rows_out

    def summary(self) -> str:
        lines = [
            f"Rows in      : {self.n_rows_in:,}",
            f"Rows out     : {self.n_rows_out:,} (dropped {self.n_dropped:,})",
        ]
        if self.errors:
            lines.append("Errors (rows dropped):")
            lines += [f"  - {k}: {v:,}" for k, v in self.errors.items()]
        if self.warnings:
            lines.append("Warnings (rows kept, handle in preprocessing):")
            lines += [f"  - {k}: {v:,}" for k, v in self.warnings.items()]
        for k, v in self.stats.items():
            lines.append(f"{k}: {v}")
        return "\n".join(lines)


def validate_reviews(
    df: pd.DataFrame, drop_invalid: bool = True
) -> tuple[pd.DataFrame, ValidationReport]:
    """Validate a DataFrame produced by `load_reviews`.

    Returns:
        (DataFrame filtered if drop_invalid, ValidationReport)
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    report = ValidationReport(n_rows_in=len(df))
    invalid = pd.Series(False, index=df.index)

    def flag_error(name: str, mask: pd.Series) -> None:
        nonlocal invalid
        n = int(mask.sum())
        if n:
            report.errors[name] = n
            invalid |= mask

    # ---- Errors: rows are dropped ----
    flag_error("duplicate review_id", df["review_id"].duplicated(keep="first"))
    flag_error("score outside 1-5", ~df["score"].between(1, 5))
    flag_error("helpful_yes > helpful_total", df["helpful_yes"] > df["helpful_total"])
    flag_error("negative helpfulness", (df["helpful_yes"] < 0) | (df["helpful_total"] < 0))
    flag_error("empty/null text", df["text"].isna() | (df["text"].str.len() == 0))
    flag_error("invalid review_date", df["review_date"].isna())
    flag_error("null product_id/user_id", df["product_id"].isna() | df["user_id"].isna())

    # ---- Warnings: rows are kept ----
    for col in ("profile_name", "summary"):
        n = int(df[col].isna().sum())
        if n:
            report.warnings[f"{col} null"] = n

    n_dup = int(df.duplicated(["user_id", "timestamp", "text"]).sum())
    if n_dup:
        report.warnings["duplicate content (user_id+timestamp+text)"] = n_dup

    n_short = int((df["text"].str.len() < 20).sum())
    if n_short:
        report.warnings["text too short (<20 chars)"] = n_short

    # ---- Quick stats ----
    report.stats = {
        "Date range": f"{df['review_date'].min():%Y-%m-%d} -> {df['review_date'].max():%Y-%m-%d}",
        "Unique products": f"{df['product_id'].nunique():,}",
        "Unique users": f"{df['user_id'].nunique():,}",
        "Score distribution (%)": (df["score"].value_counts(normalize=True).sort_index() * 100)
        .round(1).to_dict(),
    }

    out = df.loc[~invalid].reset_index(drop=True) if drop_invalid else df
    report.n_rows_out = len(out)
    return out, report