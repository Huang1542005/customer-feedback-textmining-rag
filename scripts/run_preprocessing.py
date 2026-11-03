"""Run the preprocessing step: clean -> deduplicate -> build features -> save.

Example:
    python scripts/run_preprocessing.py
"""
import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from customer_feedback.data_ingestion.load_reviews import save_reviews  # noqa: E402
from customer_feedback.preprocessing.build_features import build_features  # noqa: E402
from customer_feedback.preprocessing.clean_text import clean_reviews  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Preprocess validated Amazon Fine Food Reviews")
    p.add_argument("--input", default=str(ROOT / "data/interim/reviews_validated.parquet"))
    p.add_argument("--output", default=str(ROOT / "data/processed/reviews_clean.parquet"))
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    df = pd.read_parquet(args.input)
    df, stats = clean_reviews(df)
    df = build_features(df)

    print("\nPreprocessing summary")
    print(f"  Rows in             : {stats['rows_in']:,}")
    print(f"  Duplicates dropped  : {stats['dropped_duplicates']:,}")
    print(f"  Dupes after cleaning: {stats['dropped_duplicates_after_clean']:,}")
    print(f"  Too short dropped   : {stats['dropped_too_short']:,}")
    print(f"  Rows out            : {stats['rows_out']:,}")
    print(f"  Sentiment (%)       : {(df['sentiment'].value_counts(normalize=True) * 100).round(1).to_dict()}")
    print(f"  Median words/review : {int(df['word_count'].median())}")
    print(f"  Negative reviews    : {int(df['is_negative'].sum()):,}\n")

    save_reviews(df, args.output)


if __name__ == "__main__":
    main()