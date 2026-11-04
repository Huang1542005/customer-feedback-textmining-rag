"""Run unchanged branch snapshots and collect artifacts for P5.

No checkout, merge, cherry-pick, or modification of upstream source is performed.
Snapshots live under ignored artifacts/. P5 itself only reads their output files.
"""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-c", f"safe.directory={ROOT.as_posix()}", *args], cwd=ROOT)


def snapshot(ref: str, destination: Path) -> str:
    commit = git("rev-parse", ref).decode().strip()
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(git("archive", "--format=zip", commit))) as archive:
        for info in archive.infolist():
            target = (destination / info.filename).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError("Unsafe archive member")
        archive.extractall(destination)
    return commit


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reviews", type=Path, required=True)
    p.add_argument("--nrows", type=int, default=None, help="Limit raw rows; omit to process the full CSV")
    p.add_argument("--max-rag-reviews", type=int, default=1000)
    p.add_argument("--skip-rag", action="store_true", help="Keep P4 explicitly missing, never fabricate evidence")
    p.add_argument("--provider", choices=("local", "gemini"), default="local")
    p.add_argument("--rag-ref", default="origin/feature/rag")
    p.add_argument("--mining-ref", default="origin/feature/text-mining")
    p.add_argument("--output-dir", type=Path, default=ROOT / "data/processed")
    args = p.parse_args()
    if not args.reviews.is_file():
        p.error(f"CSV not found: {args.reviews}")
    if (args.nrows is not None and args.nrows < 1) or args.max_rag_reviews < 1:
        p.error("Row limits must be positive")
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    # Refuse to mix an older run with new outputs.
    if any(out.iterdir()):
        p.error("Output directory must be empty; choose a new directory for each upstream run")
    refs = {}
    sources = {}
    for kind, ref in (("rag", args.rag_ref), ("mining", args.mining_ref)):
        commit = git("rev-parse", ref).decode().strip()
        sources[kind] = ROOT / "artifacts/upstream" / commit
        refs[ref] = snapshot(ref, sources[kind])
    base = sources["rag"]
    env = dict(os.environ, PYTHONPATH=str(base / "src"))

    def run(script: Path, *arguments: str) -> None:
        subprocess.run([sys.executable, str(script), *map(str, arguments)],
                       cwd=ROOT, env=env, check=True)

    validated = ROOT / "artifacts/upstream_runs" / out.name / "reviews_validated.parquet"
    ingestion_args = ["--input", str(args.reviews.resolve()), "--output", str(validated)]
    if args.nrows is not None:
        ingestion_args += ["--nrows", str(args.nrows)]
    run(base / "scripts/run_ingestion.py", *ingestion_args)
    run(base / "scripts/run_preprocessing.py", "--input", str(validated),
        "--output", str(out / "reviews_clean.parquet"))
    run(base / "scripts/run_issue_analysis.py", "--input", str(out / "reviews_clean.parquet"), "--outdir", str(out))
    run(sources["mining"] / "src/customer_feedback/text_mining/trend_analysis.py",
        "--reviews", str(out / "reviews_clean.parquet"), "--assignments", str(out / "issue_assignments.parquet"),
        "--outdir", str(out))
    if not args.skip_rag:
        run(ROOT / "scripts/export_p4_outputs.py", "--upstream-root", str(base),
            "--input-dir", str(out), "--max-reviews", str(args.max_rag_reviews), "--provider", args.provider)
    provenance = {"upstream_commits": refs, "raw_file": args.reviews.name,
                  "raw_size_bytes": args.reviews.stat().st_size, "raw_row_limit": args.nrows,
                  "rag_review_limit": args.max_rag_reviews, "rag_status": "skipped" if args.skip_rag else "completed",
                  "trend_window_months": 3, "priority_window_months": 12,
                  "notes": ["Source files were exported without edits.",
                            "No standalone sentiment.parquet is supplied by current branches; labels come from ratings.",
                            "P3 priority growth and P2 trend growth use different windows and denominators."]}
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print(f"Unchanged upstream outputs collected at {out}")


if __name__ == "__main__":
    main()
