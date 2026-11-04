"""P5 contract, source preservation, traceability and missing-data checks."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from customer_feedback.reporting.artifacts import load_bundle
from customer_feedback.reporting.analyst import attach_analysis
from customer_feedback.reporting.generate_report import build_reports, evaluate, generate
from customer_feedback.reporting.llm import validate_claims


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inputs = self.root / "inputs"
        self.inputs.mkdir()
        self.issue = {"issue_id": 0, "rank": 1, "label": "broken packaging", "priority_score": 80,
                      "top_terms": ["broken", "box"],
                      "metrics": {"n_reviews": 1, "pct_one_star": 1.0},
                      "examples": [{"review_id": 11, "text": "The box was broken."}]}
        self.write_json("issues_ranked.json", [self.issue])
        with (self.inputs / "reviews_clean.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["review_id", "review_text", "score", "sentiment"])
            writer.writeheader()
            writer.writerows([{"review_id": 11, "review_text": "The box was broken.", "score": 1, "sentiment": "negative"},
                              {"review_id": 12, "review_text": "Great taste.", "score": 5, "sentiment": "positive"}])

    def write_json(self, name, value):
        (self.inputs / name).write_text(json.dumps(value), encoding="utf-8")

    def test_real_branch_names_and_input_files_are_preserved(self):
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.inputs.iterdir()}
        payload = generate(self.inputs, self.root / "reports")
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.inputs.iterdir()}
        self.assertEqual(before, after)
        self.assertEqual(payload["reports"][0]["issue_id"], 0)
        self.assertEqual(payload["sentiment"]["counts"]["negative"], 1)
        self.assertTrue((self.root / "reports/reports.md").is_file())
        self.assertTrue((self.root / "reports/evaluation.json").is_file())

    def test_missing_p4_does_not_invent_retrieval_or_root_cause(self):
        bundle = load_bundle(self.inputs)
        payload = build_reports(bundle)
        self.assertIn("Not established", payload["reports"][0]["root_cause"])
        self.assertEqual(evaluate(payload, bundle)["issues_with_p4_evidence"], 0)
        self.assertEqual(payload["reports"][0]["citations"][0]["origin"], "p3_example")
        self.assertEqual(evaluate(payload, bundle)["retrieval_quality"]["status"], "not_evaluated")

    def test_fabricated_quotes_and_policy_titles_are_not_verified(self):
        self.write_json("rag_insights.json", [{"issue_id": 0, "citations": [
            {"type": "review", "id": "Review #11", "snippet": "The warehouse caused damage."},
            {"type": "review", "id": "Review #999", "snippet": "A nonexistent review"},
            {"type": "policy", "id": "POL-FAKE", "source": "Packaging policy"}]}])
        payload = build_reports(load_bundle(self.inputs))
        self.assertEqual(sum(c["verified"] for c in payload["reports"][0]["citations"]), 1)

    def test_chunk_and_truncated_quotes_resolve_and_positive_evidence_warns(self):
        self.write_json("retrieval_results.json", [{"issue_id": 0, "evidence_reviews": [
            {"doc_id": "rev_12_c1", "text": "Great taste.", "metadata": {"review_id": 12}},
        ], "relevant_policies": [{"text": "Inspect damaged packages.", "metadata": {
            "source": "policy", "policy_id": "POL-1", "file_name": "policy.md"}}]}])
        self.write_json("rag_insights.json", [{"issue_id": 0, "citations": [
            {"type": "review", "id": "Review #11", "snippet": "The box..."}]}])
        report = build_reports(load_bundle(self.inputs))["reports"][0]
        self.assertTrue(all(c["verified"] for c in report["citations"]))
        self.assertTrue(any("4–5-star reviews" in w for w in report["warnings"]))

    def test_duplicate_ids_and_ambiguous_handoffs_fail(self):
        self.write_json("issues_ranked.json", [self.issue, self.issue])
        with self.assertRaisesRegex(ValueError, "Duplicate issue_id"):
            load_bundle(self.inputs)
        self.write_json("issues.json", [self.issue])
        with self.assertRaisesRegex(ValueError, "Ambiguous issues"):
            load_bundle(self.inputs)

    def test_missing_metric_is_not_replaced_with_zero(self):
        self.issue["metrics"] = {}
        self.issue.pop("priority_score")
        self.write_json("issues_ranked.json", [self.issue])
        payload = build_reports(load_bundle(self.inputs))
        self.assertIsNone(payload["reports"][0]["priority_score"])
        self.assertEqual(payload["reports"][0]["facts"], [])

    def test_bad_metric_rejected(self):
        self.issue["metrics"]["pct_one_star"] = 72
        self.write_json("issues_ranked.json", [self.issue])
        with self.assertRaisesRegex(ValueError, "pct_one_star"):
            build_reports(load_bundle(self.inputs))

    def test_llm_must_cite_resolved_evidence(self):
        valid = {"claims": [{"text": "Investigate packaging damage.", "citation_ids": ["Review #11"]}]}
        self.assertEqual(len(validate_claims(valid, {"Review #11"})), 1)
        valid["claims"][0]["citation_ids"] = ["POL-FAKE"]
        with self.assertRaises(ValueError):
            validate_claims(valid, {"Review #11"})

    def test_output_cannot_overwrite_input_directory(self):
        with self.assertRaisesRegex(ValueError, "must differ"):
            generate(self.inputs, self.inputs)

    def test_assignment_integrity_and_source_scope_are_reported(self):
        with (self.inputs / "issue_assignments.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["review_id", "issue_id"])
            writer.writeheader()
            writer.writerows([{"review_id": 11, "issue_id": 0}, {"review_id": 999, "issue_id": 3}])
        self.write_json("provenance.json", {"raw_row_limit": 1000})
        bundle = load_bundle(self.inputs)
        checks = evaluate(build_reports(bundle), bundle)
        self.assertEqual(checks["orphan_review_assignments"], 1)
        self.assertEqual(checks["orphan_issue_assignments"], 1)
        self.assertTrue(any("Partial dataset" in w for w in bundle["warnings"]))

    def test_authored_analysis_requires_matching_inputs_and_resolved_citations(self):
        payload = build_reports(load_bundle(self.inputs))
        analysis = {"method": "assistant_authored_evidence_synthesis", "scope": "Test analysis",
                    "source_fingerprints": {r["kind"]: r["sha256"] for r in payload["input_manifest"]},
                    "issues": [{"issue_id": 0, "observations": [
                        {"text": "Customer reports a broken box.", "citation_ids": ["Review #11"]}]}]}
        path = self.root / "analysis.json"
        path.write_text(json.dumps(analysis), encoding="utf-8")
        attach_analysis(payload, path)
        self.assertIn("analyst_insight", payload["reports"][0])
        analysis["issues"][0]["observations"][0]["citation_ids"] = ["Review #999"]
        path.write_text(json.dumps(analysis), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unresolved citations"):
            attach_analysis(payload, path)
        analysis["source_fingerprints"]["issues"] = "stale"
        path.write_text(json.dumps(analysis), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "different input artifacts"):
            attach_analysis(payload, path)


if __name__ == "__main__":
    unittest.main()
