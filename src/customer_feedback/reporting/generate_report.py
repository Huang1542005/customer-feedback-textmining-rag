"""P5: evidence-linked reports from immutable P1-P4 file hand-offs."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .artifacts import identifier, load_bundle, number, unique_index
from .citations import collect_citations


def sentiment_counts(bundle: dict) -> dict:
    rows = bundle["sentiment"] or bundle["reviews"]
    counts = {"positive": 0, "neutral": 0, "negative": 0, "unknown": 0}
    explicit = 0
    for row in rows:
        label = str(row.get("sentiment", "")).lower()
        if label in counts and label != "unknown":
            explicit += 1
        else:
            score = number(row.get("score"))
            label = "unknown" if score is None else "negative" if score <= 2 else "neutral" if score == 3 else "positive"
        counts[label] += 1
    return {"counts": counts, "source": "sentiment_output" if bundle["sentiment"] else "clean_reviews",
            "method": "provided_labels" if explicit == len(rows) and rows else "rating_proxy_or_mixed",
            "note": "Rating-derived labels are a proxy, not an independent text sentiment evaluation."}


def build_reports(bundle: dict) -> dict[str, Any]:
    reviews = unique_index(bundle["reviews"], "review_id")
    retrieval = unique_index(bundle["retrieval"], "issue_id")
    upstream = unique_index(bundle["upstream_insights"], "issue_id")
    reports = []
    for issue in bundle["issues"]:
        key = identifier(issue["issue_id"])
        metrics = dict(issue.get("metrics") or {})
        count = number(metrics.get("n_reviews"))
        severity = number(metrics.get("pct_one_star"))
        priority = number(issue.get("priority_score"))
        if priority is not None and not 0 <= priority <= 100:
            raise ValueError(f"Issue {key}: priority_score outside 0..100")
        if severity is not None and not 0 <= severity <= 1:
            raise ValueError(f"Issue {key}: pct_one_star outside 0..1")
        citations = collect_citations(issue, retrieval.get(key, {}), upstream.get(key, {}), reviews)
        verified = [c for c in citations if c["verified"]]
        patterns = [r for r in bundle["patterns"] if str(r.get("issue_id")) == key]
        trends = [r for r in bundle["trends"] if str(r.get("issue_id")) == key]
        facts = []
        if count is not None:
            facts.append({"text": f"P3 assigned {count:g} complaint reviews to this issue.", "source": "issues.metrics.n_reviews"})
        if severity is not None:
            facts.append({"text": f"{severity:.1%} of assigned complaints are one-star reviews.", "source": "issues.metrics.pct_one_star"})
        if priority is not None:
            facts.append({"text": f"P3 priority score: {priority:g}/100.", "source": "issues.priority_score"})
        share = number(metrics.get("share_of_complaints"))
        if share is not None:
            facts.append({"text": f"This group accounts for {share:.1%} of complaints assigned by P3.",
                          "source": "issues.metrics.share_of_complaints"})
        if patterns:
            latest = sorted(patterns, key=lambda row: str(row.get("month", "")))[-1]
            status = str(latest.get("trend_status", "unknown"))
            facts.append({"text": f"P2 trend status in {latest.get('month', 'latest period')}: {status}.",
                          "source": "patterns.trend_status"})
            recent_growth = number(latest.get("growth_rate"))
            if recent_growth is not None:
                facts.append({"text": f"P2 rolling-window share growth: {recent_growth:+.1%} (separate from P3 growth).",
                              "source": "patterns.growth_rate"})
        warnings = []
        if not retrieval.get(key):
            warnings.append("No P4 retrieval output for this issue; P3 examples are displayed separately.")
        if not verified:
            warnings.append("No resolved evidence; a root cause cannot be established.")
        if any(not c["verified"] for c in citations):
            warnings.append("Some citations could not be resolved and are excluded from recommendations.")
        if any(number(c.get("score"), 0) >= 4 for c in verified if c["type"] == "review"):
            warnings.append("Retrieved evidence includes 4–5-star reviews; inspect text rather than inferring sentiment from rating alone.")
        recommendations = ["Review the cited complaints and verify the defect before assigning a root cause.",
                           "Compare the next reporting period using the same cohort and trend window."]
        if any(c["type"] == "policy" for c in verified):
            recommendations.append("Check the retrieved policy sections before choosing corrective actions.")
        negative_evidence = [c["id"] for c in verified if c["type"] == "review"
                             and number(c.get("score"), 5) <= 2]
        if negative_evidence:
            recommendations.insert(0, "Inspect the reported defect in " + ", ".join(dict.fromkeys(negative_evidence))
                                   + "; verify whether these complaints describe the same failure mode.")
        if patterns and status in {"increasing", "new_or_emerging"}:
            recommendations.append("Escalate trend review: P2 flags this issue as " + status
                                   + "; confirm volume and the comparison window before intervention.")
        reports.append({
            "issue_id": issue["issue_id"], "rank": issue.get("rank"),
            "label": str(issue.get("label", key)), "priority_score": priority,
            "top_terms": issue.get("top_terms", []), "metrics": metrics,
            "facts": facts, "root_cause": "Not established by the supplied evidence; requires investigation.",
            "recommendations": recommendations, "citations": citations,
            "trend_summary": patterns, "trends": trends, "warnings": warnings,
            "generation": {"provider": "deterministic", "status": "completed"},
            "upstream_narrative": upstream.get(key, {}).get("root_cause"),
        })
    reports.sort(key=lambda r: (number(r.get("rank"), float("inf")),
                                -number(r.get("priority_score"), -1), str(r["issue_id"])))
    dates = sorted(str(r["review_date"])[:10] for r in bundle["reviews"] if r.get("review_date"))
    return {"schema_version": "1.0", "generated_at": datetime.now(timezone.utc).isoformat(),
            "input_manifest": bundle["manifest"], "warnings": bundle["warnings"],
            "provenance": bundle.get("provenance", {}),
            "review_period": {"start": dates[0] if dates else None, "end": dates[-1] if dates else None},
            "sentiment": sentiment_counts(bundle), "reports": reports}


def evaluate(payload: dict, bundle: dict) -> dict:
    reports = payload["reports"]
    citations = [c for r in reports for c in r["citations"]]
    valid = [c for c in citations if c["verified"]]
    review_ids = set(unique_index(bundle["reviews"], "review_id"))
    assignments = bundle["clusters"]
    orphan = sum(str(r["review_id"]) not in review_ids for r in assignments)
    issue_ids = {str(r["issue_id"]) for r in reports}
    orphan_issues = sum(str(r.get("issue_id")) not in issue_ids and str(r.get("issue_id")) != "-1"
                        for r in assignments)
    return {
        "scope": "Artifact integrity and evidence traceability, not semantic correctness or retrieval relevance.",
        "issue_count": len(reports), "citation_count": len(citations),
        "issues_with_authored_insight": sum("analyst_insight" in r for r in reports),
        "resolved_citation_count": len(valid),
        "citation_resolution_rate": len(valid) / len(citations) if citations else None,
        "issues_with_resolved_evidence": sum(any(c["verified"] for c in r["citations"]) for r in reports),
        "issues_with_p4_evidence": sum(any(c["verified"] and c["origin"] == "p4_output" for c in r["citations"]) for r in reports),
        "assignment_count": len(assignments), "orphan_review_assignments": orphan if review_ids else None,
        "orphan_issue_assignments": orphan_issues,
        "retrieval_quality": {"status": "not_evaluated", "reason": "No query relevance labels supplied by P4."},
        "semantic_faithfulness": {"status": "not_evaluated", "reason": "Requires claim-level human or independently validated evaluation."},
        "sentiment_accuracy": {"status": "not_evaluated", "reason": "No independent sentiment ground truth supplied."},
        "limitations": ["A resolved quotation proves traceability, not that it supports a causal claim.",
                        "Policy text is traced to the P4 output, not independently authenticated."]}


def markdown_report(payload: dict) -> str:
    lines = ["# Customer Feedback — P5 Insight Report", "", f"Generated: {payload['generated_at']}", "",
             "Root causes remain hypotheses until reviewed. Citation checks measure traceability only.", ""]
    if payload["warnings"]:
        lines += ["## Input limitations", ""] + [f"- {w}" for w in payload["warnings"]] + [""]
    analysis = payload.get("analyst_analysis")
    if analysis:
        lines += ["## Insight tổng hợp", "", analysis["scope"], ""]
        for finding in analysis["executive_findings"]:
            lines += [f"### {finding['title']}", "", finding["text"], "",
                      "Hành động đề xuất: " + finding["action"], ""]
            if finding.get("citation_ids"):
                lines += ["Nguồn: " + ", ".join(finding["citation_ids"]), ""]
        lines += ["### Giới hạn diễn giải", ""] + [f"- {w}" for w in analysis["limitations"]] + [""]
    for report in payload["reports"]:
        lines += [f"## #{report['rank']} — {report['label']}", ""]
        lines += [f"- {fact['text']}" for fact in report["facts"]]
        authored = report.get("analyst_insight")
        if authored:
            lines += ["", "### " + authored["headline"], ""]
            for observation in authored["observations"]:
                lines += [observation["text"] + " [" + ", ".join(observation["citation_ids"]) + "]", ""]
            lines += ["**Diễn giải:** " + authored["interpretation"], "",
                      "**Chưa thể kết luận:** " + authored["uncertainty"], "", "**Hành động đề xuất:**", ""]
            lines += ["- " + action for action in authored["actions"]] + [""]
        if not authored:
            lines += ["", "### Investigation", "", report["root_cause"], "", "### Recommended next steps", ""]
            lines += [f"- {text}" for text in report["recommendations"]]
        lines += ["", "### Evidence", ""]
        for citation in report["citations"]:
            status = "resolved" if citation["verified"] else "unresolved"
            lines.append(f"- [{citation['id']}] ({status}, {citation['origin']}): {citation['quote']}")
        if report.get("llm_claims"):
            lines += ["", "### Generated hypotheses — require review", ""]
            lines += [f"- {c['text']} [{', '.join(c['citation_ids'])}]" for c in report["llm_claims"]]
        lines += [""] + [f"> {w}" for w in report["warnings"]] + [""]
    return "\n".join(lines)


def generate(input_dir: str | Path, output_dir: str | Path, provider: str = "offline",
             model: str | None = None, analysis_file: str | Path | None = None) -> dict:
    bundle = load_bundle(input_dir)
    payload = build_reports(bundle)
    if provider == "gemini":
        from .llm import enrich_reports
        enrich_reports(payload, model=model)
    elif provider != "offline":
        raise ValueError(f"Unknown provider: {provider}")
    if analysis_file:
        from .analyst import attach_analysis
        attach_analysis(payload, analysis_file)
    evaluation = evaluate(payload, bundle)
    output_dir = Path(output_dir)
    if output_dir.resolve() == Path(input_dir).resolve():
        raise ValueError("Output directory must differ from the upstream input directory.")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in (("reports.json", payload), ("evaluation.json", evaluation)):
        (output_dir / name).write_text(json.dumps(content, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    (output_dir / "reports.md").write_text(markdown_report(payload), encoding="utf-8")
    return payload
