"""Generate P5 artifacts from existing P1-P4 outputs only."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from customer_feedback.reporting.generate_report import generate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=ROOT / "data/processed")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports/p5")
    parser.add_argument("--provider", choices=("offline", "gemini"), default="offline")
    parser.add_argument("--model", help="Gemini model, alternatively GEMINI_MODEL environment variable")
    parser.add_argument("--analysis-file", type=Path, help="Optional authored insight JSON, matched against input SHA-256")
    args = parser.parse_args()
    try:
        payload = generate(args.input_dir, args.output_dir, provider=args.provider, model=args.model,
                           analysis_file=args.analysis_file)
    except (ValueError, FileNotFoundError, ImportError) as error:
        parser.exit(1, f"P5: {error}\n")
    print(f"Generated {len(payload['reports'])} reports in {args.output_dir}")


if __name__ == "__main__":
    main()
