"""Attach a versioned, authored analysis without changing upstream outputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def attach_analysis(payload: dict, path: str | Path) -> None:
    path = Path(path)
    content = path.read_bytes()
    analysis = json.loads(content.decode("utf-8-sig"))
    fingerprints = {item["kind"]: item["sha256"] for item in payload["input_manifest"]}
    expected = analysis.get("source_fingerprints", {})
    if not expected or any(fingerprints.get(kind) != digest for kind, digest in expected.items()):
        raise ValueError("Authored analysis belongs to different input artifacts; review it before reuse.")
    by_issue = {str(report["issue_id"]): report for report in payload["reports"]}
    entries = analysis.get("issues", [])
    if not isinstance(entries, list) or len({str(row["issue_id"]) for row in entries}) != len(entries):
        raise ValueError("Authored analysis must have unique issue IDs")
    global_ids = {citation["id"] for report in payload["reports"] for citation in report["citations"]
                  if citation["verified"]}
    for finding in analysis.get("executive_findings", []):
        if any(ref not in global_ids for ref in finding.get("citation_ids", [])):
            raise ValueError("Executive finding references unresolved evidence")
    for entry in entries:
        report = by_issue.get(str(entry["issue_id"]))
        if report is None:
            raise ValueError(f"Authored analysis references unknown issue {entry['issue_id']}")
        allowed = {c["id"] for c in report["citations"] if c["verified"]}
        claims = entry.get("observations", [])
        if not claims or any(not claim.get("citation_ids") or
                             any(ref not in allowed for ref in claim["citation_ids"]) for claim in claims):
            raise ValueError(f"Authored analysis for issue {entry['issue_id']} has unresolved citations")
        report["analyst_insight"] = entry
    payload["analyst_analysis"] = {
        "method": analysis["method"], "scope": analysis["scope"],
        "executive_findings": analysis.get("executive_findings", []),
        "limitations": analysis.get("limitations", []),
        "file": path.name, "sha256": hashlib.sha256(content).hexdigest(),
        "note": "Authored synthesis by the assistant; not independent human validation or an automatically rerun model.",
    }
