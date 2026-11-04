"""Answer and insight generation module for Customer Feedback RAG.

Synthesizes issue metrics, customer review evidence, and policy standards
into actionable reports with verifiable citations.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

from customer_feedback.rag.retrieval import RetrievedContext

logger = logging.getLogger(__name__)


@dataclass
class IssueInsight:
    """Actionable insight and recommendation generated for an issue."""

    issue_id: int
    rank: int
    label: str
    priority_score: float
    root_cause: str
    impact_assessment: str
    recommendations: list[str] = field(default_factory=list)
    citations: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "rank": self.rank,
            "label": self.label,
            "priority_score": self.priority_score,
            "root_cause": self.root_cause,
            "impact_assessment": self.impact_assessment,
            "recommendations": self.recommendations,
            "citations": self.citations,
        }


class RAGGenerator:
    """Generates structured insights using LLM or offline fallback."""

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        api_key: str | None = None,
    ):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None

        if self.api_key:
            try:
                from google import genai

                self.client = genai.Client(api_key=self.api_key)
                logger.info("Initialized Gemini client for model %s", model_name)
            except Exception as e:
                logger.warning("Could not initialize Gemini client: %s. Using offline generator.", e)

    def generate_insight(
        self,
        issue: dict[str, Any],
        context: RetrievedContext,
    ) -> IssueInsight:
        """Generate root-cause analysis and policy-backed recommendations."""
        if self.client:
            try:
                return self._generate_with_gemini(issue, context)
            except Exception as e:
                logger.warning("Gemini generation failed: %s. Falling back to structured synthesis.", e)

        return self._generate_offline(issue, context)

    def _build_prompt(self, issue: dict[str, Any], context: RetrievedContext) -> str:
        reviews_block = "\n".join(
            [
                f"- [Review #{doc.metadata.get('review_id', doc.doc_id)}] (Score: {doc.metadata.get('score', 'N/A')}/5, "
                f"Product: {doc.metadata.get('product_id', 'N/A')}): \"{doc.text}\""
                for doc in context.evidence_reviews
            ]
        )

        policies_block = "\n".join(
            [
                f"### {doc.metadata.get('policy_id', 'Policy')}: {doc.metadata.get('section_title', '')}\n{doc.text}"
                for doc in context.relevant_policies
            ]
        )

        prompt = f"""You are an expert Customer Experience & Quality Assurance Director.
Analyze this high-priority customer issue detected from negative feedback:

ISSUE SUMMARY:
- Rank: #{issue.get('rank', 'N/A')}
- Issue Label: {issue.get('label', 'Unknown')}
- Priority Score: {issue.get('priority_score', 'N/A')}/100
- Complaint Share: {issue.get('metrics', {}).get('share_of_complaints', 'N/A')}
- 1-Star Review Rate: {issue.get('metrics', {}).get('pct_one_star', 'N/A')}
- Growth Trend: {issue.get('metrics', {}).get('growth_recent_vs_prev', 'N/A')}

CUSTOMER FEEDBACK EVIDENCE:
{reviews_block or "No specific review evidence retrieved."}

OPERATIONAL & QUALITY POLICIES:
{policies_block or "No policy documents matched."}

TASK:
Provide an executive, evidence-based insight report formatted with:
1. Root Cause Analysis: Identify the fundamental defect or operational breakdown.
2. Impact Assessment: Evaluate business, customer churn, and compliance risks.
3. Actionable Recommendations: Concrete steps aligned with policies (e.g. supplier audit, packaging prep-hold, refund SLAs).
4. Citations: Explicitly cite which Review #[ID] and Policy sections support each point.
"""
        return prompt

    def _generate_with_gemini(self, issue: dict[str, Any], context: RetrievedContext) -> IssueInsight:
        prompt = self._build_prompt(issue, context)
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        text = response.text or ""

        # Extract citations
        citations = []
        for doc in context.evidence_reviews:
            r_id = doc.metadata.get("review_id", doc.doc_id)
            citations.append({"type": "review", "id": f"Review #{r_id}", "source": doc.text[:100] + "..."})
        for doc in context.relevant_policies:
            p_id = doc.metadata.get("policy_id", doc.doc_id)
            citations.append({"type": "policy", "id": p_id, "source": doc.metadata.get("title", "")})

        return IssueInsight(
            issue_id=int(issue.get("issue_id", 0)),
            rank=int(issue.get("rank", 0)),
            label=str(issue.get("label", "")),
            priority_score=float(issue.get("priority_score", 0.0)),
            root_cause=text,
            impact_assessment=f"High priority defect with score {issue.get('priority_score')}.",
            recommendations=["Refer to LLM detailed response above."],
            citations=citations,
        )

    def _generate_offline(self, issue: dict[str, Any], context: RetrievedContext) -> IssueInsight:
        """Deterministic offline synthesizer when LLM API key is not configured."""
        label = issue.get("label", "General Quality Defect")
        top_terms = issue.get("top_terms", [])
        metrics = issue.get("metrics", {})
        score = issue.get("priority_score", 0.0)

        # Infer defect type from terms
        terms_str = " ".join(top_terms).lower()
        if any(w in terms_str for w in ["box", "broken", "package", "leak", "crushed", "shipped"]):
            defect_type = "Packaging integrity & courier transit damage"
            policy_rec = "Enforce POL-PKG-001 (Edge Crush Test packaging, bubble wrap, torque-sealed lids)."
        elif any(w in terms_str for w in ["stale", "expired", "taste", "smell", "bad", "odor", "date"]):
            defect_type = "Shelf life expiration or warehouse storage degradation"
            policy_rec = "Trigger POL-FQD-002 (Inventory audit for minimum 60-day shelf life, QA barrier check)."
        else:
            defect_type = "Product specification or recipe dissatisfaction"
            policy_rec = "Apply POL-RET-003 (Returnless refund SLA, batch QA inspection)."

        root_cause = (
            f"Automated analysis indicates recurring complaints centered around '{label}' ({', '.join(top_terms)}). "
            f"The primary root cause is identified as: {defect_type}. "
            f"Reviews consistently highlight unacceptable product condition upon arrival."
        )

        impact_assessment = (
            f"Issue priority score is {score:.1f}/100 with {metrics.get('n_reviews', 'multiple')} complaints. "
            f"Approximately {float(metrics.get('pct_one_star', 0.0))*100:.1f}% of reviews were 1-star ratings, "
            f"creating severe friction and risk of customer attrition."
        )

        recommendations = [
            f"Operational Compliance: {policy_rec}",
            "Customer Support: Activate instant returnless refunds per POL-RET-001 for affected accounts.",
            "Supplier Feedback: Flag defect logs to manufacturer QA for packaging or formulation review.",
        ]

        citations = []
        for doc in context.evidence_reviews[:3]:
            r_id = doc.metadata.get("review_id", doc.doc_id)
            citations.append({"type": "review", "id": f"Review #{r_id}", "snippet": doc.text[:120] + "..."})
        for doc in context.relevant_policies[:2]:
            p_id = doc.metadata.get("policy_id", doc.doc_id)
            citations.append({"type": "policy", "id": p_id, "title": doc.metadata.get("title", "")})

        return IssueInsight(
            issue_id=int(issue.get("issue_id", 0)),
            rank=int(issue.get("rank", 0)),
            label=label,
            priority_score=score,
            root_cause=root_cause,
            impact_assessment=impact_assessment,
            recommendations=recommendations,
            citations=citations,
        )

