
import pandas as pd

from customer_feedback.text_mining.clustering import evaluate_clustering
from customer_feedback.text_mining.trend_analysis import analyze_trends


def test_clustering_returns_three_algorithms():
    rows = []
    for i in range(40):
        rows.append({
            "review_id": i,
            "score": 1,
            "text_normalized": "broken damaged leaking box shipping",
            "review_text": "The box was broken and leaking.",
        })
        rows.append({
            "review_id": 100 + i,
            "score": 2,
            "text_normalized": "bitter stale taste flavor expired",
            "review_text": "The food tasted stale and bitter.",
        })

    df = pd.DataFrame(rows)
    metrics, topics, assignments = evaluate_clustering(
        df, n_clusters=2, sample_size=80
    )

    assert set(metrics["algorithm"]) == {
        "KMeans", "MiniBatchKMeans", "Agglomerative"
    }
    assert len(assignments) == 80 * 3
    assert not topics.empty
    assert metrics["silhouette_cosine"].notna().all()


def test_trend_detects_growing_issue():
    rows = []
    assigned = []
    review_id = 1

    for month in range(1, 7):
        first_count = 2 if month <= 3 else 8
        second_count = 8 if month <= 3 else 2

        for issue_id, count in [(0, first_count), (1, second_count)]:
            for _ in range(count):
                rows.append({
                    "review_id": review_id,
                    "score": 1,
                    "review_date": pd.Timestamp(
                        year=2020, month=month, day=15
                    ),
                })
                assigned.append({
                    "review_id": review_id,
                    "issue_id": issue_id,
                })
                review_id += 1

    monthly, latest = analyze_trends(
        pd.DataFrame(rows),
        pd.DataFrame(assigned),
        window=3,
        min_count=1,
    )

    issue_zero = latest.set_index("issue_id").loc[0]
    assert issue_zero["trend_status"] == "increasing"
    assert issue_zero["growth_rate"] > 0
    assert len(monthly) == 12
