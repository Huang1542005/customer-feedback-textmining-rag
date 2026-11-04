"""Run the data ingestion step: load -> validate -> save.

Examples:
    python scripts/run_ingestion.py
    python scripts/run_ingestion.py --input data/raw/Reviews.csv --sample 0.1
"""
import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from customer_feedback.data_ingestion.load_reviews import load_reviews, save_reviews  # noqa: E402
from customer_feedback.data_ingestion.validate_data import validate_reviews  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Data ingestion for Amazon Fine Food Reviews")
    p.add_argument("--input", default=str(ROOT / "data/Reviews.csv"))
    p.add_argument("--output", default=str(ROOT / "data/interim/reviews_validated.parquet"))
    p.add_argument("--nrows", type=int, default=None, help="Read only the first N rows (debug)")
    p.add_argument("--sample", type=float, default=None, help="Random sample fraction, e.g. 0.1 = 10%%")
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    df = load_reviews(args.input, nrows=args.nrows, sample_frac=args.sample)
    df, report = validate_reviews(df, drop_invalid=True)
    print("\n" + report.summary() + "\n")
    save_reviews(df, args.output)


if __name__ == "__main__":
    main()