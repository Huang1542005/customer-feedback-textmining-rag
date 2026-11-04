import numpy as np
import pandas as pd
import pytest

from customer_feedback.issue_analysis.calculate_priority import (
    DEFAULT_WEIGHTS,
    build_issue_report,
    calculate_priority,
    summarize_issues,
)
from customer_feedback.issue_analysis.detect_issues import (
    IssueConfig,
    detect_issues,
    evaluate_issues,
)

SHIPPING = ["package", "arrived", "broken", "box", "damaged", "crushed", "leaking", "late"]
TASTE = ["bitter", "stale", "bland", "aftertaste", "expired", "tasteless", "chalky"]
POSITIVE = ["delicious", "great", "love", "tasty", "fresh", "perfect", "excellent"]


def _synthetic(seed=0):
    rng = np.random.default_rng(seed)
    rows = []

    def add(vocab, n, score, start_id, group):
        for i in range(n):
            text = " ".join(rng.choice(vocab, 6))
            rows.append(
                dict(
                    review_id=start_id + i, product_id=f"P{rng.integers(0, 30)}", score=score,
                    text_normalized=text, review_text=text, word_count=25,
                    helpful_yes=int(rng.integers(0, 5)), group=group,
                    review_date=pd.Timestamp("2012-01-01") + pd.Timedelta(days=int(rng.integers(0, 300))),
                )
            )

    add(SHIPPING, 80, 1, 0, "shipping")
    add(TASTE, 60, 2, 1000, "taste")
    add(POSITIVE, 200, 5, 2000, "positive")
    return pd.DataFrame(rows)


CFG = dict(n_issues=2, min_df=3, min_log_odds=0.3, max_features=1000)


@pytest.mark.parametrize("method", ["nmf", "kmeans"])
def test_detect_issues_separates_themes(method):
    df = _synthetic()
    res = detect_issues(df, IssueConfig(method=method, **CFG))

    merged = res.assignments.merge(df[["review_id", "group"]], on="review_id")
    assert set(merged["group"]) == {"shipping", "taste"}  # positives are never complaints
    purity = merged.groupby("group")["issue_id"].agg(lambda s: s.value_counts(normalize=True).iloc[0])
    assert (purity > 0.9).all()
    # the two themes land in different issues
    assert merged.groupby("group")["issue_id"].agg(lambda s: s.mode().iloc[0]).nunique() == 2
    # issue 0 is the largest group
    assert (merged["issue_id"] == 0).sum() >= (merged["issue_id"] == 1).sum()


def test_detect_issues_labels_use_issue_words():
    res = detect_issues(_synthetic(), IssueConfig(**CFG))
    all_terms = {t for terms in res.issues["top_terms"] for t in terms}
    assert all_terms & set(SHIPPING) and all_terms & set(TASTE)
    assert not all_terms & set(POSITIVE)  # positive-review words are filtered out


def test_detect_issues_rejects_unknown_method():
    with pytest.raises(ValueError):
        detect_issues(_synthetic(), IssueConfig(method="lda", **CFG))


def test_evaluate_issues_keys_and_ranges():
    res = detect_issues(_synthetic(), IssueConfig(**CFG))
    m = evaluate_issues(res)
    assert -1 <= m["silhouette_cosine"] <= 1 and 0 <= m["size_balance"] <= 1


def _summary(**over):
    base = pd.DataFrame(
        {
            "issue_id": [0, 1, 2],
            "share": [0.5, 0.3, 0.2],
            "pct_one_star": [0.7, 0.6, 0.5],
            "growth": [0.0, 0.0, 0.0],
            "avg_helpful_votes": [3.0, 2.0, 1.0],
        }
    )
    for k, v in over.items():
        base[k] = v
    return base


def test_priority_orders_by_components():
    out = calculate_priority(_summary())
    assert list(out["issue_id"]) == [0, 1, 2]
    assert list(out["rank"]) == [1, 2, 3]
    assert out["priority_score"].between(0, 100).all()


def test_priority_trend_rewards_only_growth():
    # issue 2 is smallest but exploding; flat/declining issues get no trend credit
    out = calculate_priority(_summary(growth=[-0.4, 0.0, 1.5]), {"trend": 1.0})
    assert out.set_index("issue_id")["trend"].to_dict() == {0: 0.0, 1: 0.0, 2: 1.0}
    assert out.iloc[0]["issue_id"] == 2


def test_priority_weights_are_normalized_and_validated():
    a = calculate_priority(_summary(), {"volume": 1, "severity": 1})
    b = calculate_priority(_summary(), {"volume": 10, "severity": 10})
    assert np.allclose(a["priority_score"], b["priority_score"])
    with pytest.raises(ValueError):
        calculate_priority(_summary(), {"volume": 1, "typo": 1})


def test_summarize_and_report_end_to_end():
    df = _synthetic()
    res = detect_issues(df, IssueConfig(**CFG))
    summary = summarize_issues(df, res.assignments, recent_months=3)
    assert summary["n_reviews"].sum() == (res.assignments["issue_id"] >= 0).sum()
    assert np.isclose(summary["share"].sum(), 1.0)

    report = build_issue_report(df, res.assignments, res.issues, n_examples=2)
    assert [r["rank"] for r in report] == [1, 2]
    assert set(report[0]["components"]) == set(DEFAULT_WEIGHTS)
    assert 1 <= len(report[0]["examples"]) <= 2