
"""Load Reviews.csv (Amazon Fine Food Reviews) and normalize its schema.

This step ONLY does: read -> rename columns -> cast dtypes -> trim whitespace.
Text cleaning (lowercasing, HTML removal, deduplication, ...) belongs in `preprocessing/`.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Original column -> standardized column (snake_case)
COLUMN_MAP: dict[str, str] = {
    "Id": "review_id",
    "ProductId": "product_id",
    "UserId": "user_id",
    "ProfileName": "profile_name",
    "HelpfulnessNumerator": "helpful_yes",
    "HelpfulnessDenominator": "helpful_total",
    "Score": "score",
    "Time": "timestamp",
    "Summary": "summary",
    "Text": "text",
}

_DTYPES = {
    "Id": "int64",
    "ProductId": "string",
    "UserId": "string",
    "ProfileName": "string",
    "HelpfulnessNumerator": "int32",
    "HelpfulnessDenominator": "int32",
    "Score": "int8",
    "Time": "int64",
    "Summary": "string",
    "Text": "string",
}

DEFAULT_RAW_PATH = Path("data/Reviews.csv")


def load_reviews(
    path: str | Path = DEFAULT_RAW_PATH,
    nrows: int | None = None,
    sample_frac: float | None = None,
    random_state: int = 42,
) -> pd.DataFrame:
    """Read raw review data and return a DataFrame with the standardized schema.

    Args:
        path: Path to Reviews.csv.
        nrows: Read only the first N rows (handy for debugging).
        sample_frac: Random sample fraction (0 < f <= 1) applied after loading.
        random_state: Seed used for sampling.

    Returns:
        DataFrame with columns: review_id, product_id, user_id, profile_name,
        helpful_yes, helpful_total, score, timestamp, summary, text, review_date.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}. "
            "Place Reviews.csv in data/raw/ or pass --input."
        )

    logger.info("Reading %s ...", path)
    df = pd.read_csv(path, dtype=_DTYPES, nrows=nrows)
    df = df.rename(columns=COLUMN_MAP)

    # Unix timestamp (seconds) -> datetime
    df["review_date"] = pd.to_datetime(df["timestamp"], unit="s")

    # Trim leading/trailing whitespace in text columns
    for col in ("profile_name", "summary", "text"):
        df[col] = df[col].str.strip()

    if sample_frac is not None:
        if not 0 < sample_frac <= 1:
            raise ValueError("sample_frac must be in the range (0, 1].")
        df = df.sample(frac=sample_frac, random_state=random_state).sort_values("review_id")
        df = df.reset_index(drop=True)

    logger.info("Loaded %d rows, %d columns.", *df.shape)
    return df


def save_reviews(df: pd.DataFrame, out_path: str | Path) -> Path:
    """Save a DataFrame as parquet (fast, preserves dtypes) or CSV, based on the file extension."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix == ".parquet":
        df.to_parquet(out_path, index=False)
    elif out_path.suffix == ".csv":
        df.to_csv(out_path, index=False)
    else:
        raise ValueError("Only .parquet or .csv output is supported.")
    logger.info("Saved %s", out_path)
    return out_path