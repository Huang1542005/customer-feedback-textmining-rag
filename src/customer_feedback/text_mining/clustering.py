
"""Compare text clustering algorithms on negative customer reviews."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.cluster import (
    KMeans,
    MiniBatchKMeans,
    AgglomerativeClustering,
)
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
)
from sklearn.preprocessing import normalize


ROOT = Path(__file__).resolve().parents[3]


def evaluate_clustering(
    reviews: pd.DataFrame,
    n_clusters: int = 12,
    sample_size: int = 2500,
    random_state: int = 42,
):
    """Compare three clustering methods on the same review sample."""

    required = {"review_id", "score", "text_normalized"}
    missing = required - set(reviews.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    mask = (
        reviews["score"].le(2)
        & reviews["text_normalized"].fillna("").str.strip().ne("")
    )
    data = reviews.loc[mask].copy()

    if data["review_id"].duplicated().any():
        raise ValueError("Duplicate review_id found")

    if sample_size <= n_clusters or n_clusters < 2:
        raise ValueError("Require sample_size > n_clusters >= 2")

    if len(data) <= n_clusters:
        raise ValueError("Not enough negative reviews")

    data = data.sample(
        n=min(sample_size, len(data)),
        random_state=random_state,
    ).reset_index(drop=True)

    # 1. TF-IDF: convert text to numerical features.
    vectorizer = TfidfVectorizer(
        max_features=12000,
        min_df=2,
        max_df=0.95,
        ngram_range=(1, 2),
        sublinear_tf=True,
    )
    X = vectorizer.fit_transform(
        data["text_normalized"].astype(str)
    )

    # 2. SVD: reduce dimensionality.
    dimensions = min(
        50,
        X.shape[0] - 1,
        X.shape[1] - 1,
    )

    if dimensions < 2:
        raise ValueError("Not enough TF-IDF features")

    svd = TruncatedSVD(
        n_components=dimensions,
        random_state=random_state,
    )
    Z = normalize(svd.fit_transform(X))

    # 3. Prepare algorithms.
    algorithms = {
        "KMeans": KMeans(
            n_clusters=n_clusters,
            n_init=10,
            random_state=random_state,
        ),
        "MiniBatchKMeans": MiniBatchKMeans(
            n_clusters=n_clusters,
            n_init=5,
            batch_size=1024,
            random_state=random_state,
        ),
        "Agglomerative": AgglomerativeClustering(
            n_clusters=n_clusters,
            linkage="ward",
        ),
    }

    metric_rows = []
    topic_rows = []
    assignment_rows = []

    feature_names = vectorizer.get_feature_names_out()

    rng = np.random.default_rng(random_state)
    evaluation_idx = rng.choice(
        len(Z),
        size=min(800, len(Z)),
        replace=False,
    )

    # 4. Train and evaluate every algorithm.
    for name, model in algorithms.items():
        labels = model.fit_predict(Z)

        unique_labels = np.unique(labels)
        valid = 2 <= len(unique_labels) < len(labels)

        if valid:
            sampled_labels = labels[evaluation_idx]
            silhouette = (
                float(
                    silhouette_score(
                        Z[evaluation_idx],
                        sampled_labels,
                        metric="cosine",
                    )
                )
                if 1 < len(np.unique(sampled_labels)) < len(sampled_labels)
                else np.nan
            )

            dbi = float(davies_bouldin_score(Z, labels))
            chi = float(calinski_harabasz_score(Z, labels))
        else:
            silhouette = np.nan
            dbi = np.nan
            chi = np.nan

        sizes = np.bincount(
            labels, minlength=n_clusters
        )

        metric_rows.append({
            "algorithm": name,
            "sample_size": len(data),
            "clusters_found": len(unique_labels),
            "silhouette_cosine": silhouette,
            "davies_bouldin": dbi,
            "calinski_harabasz": chi,
            "largest_cluster_share": sizes.max() / len(data),
        })

        # 5. Save assignments for this experimental sample.
        for review_id, cluster_id in zip(
            data["review_id"], labels
        ):
            assignment_rows.append({
                "algorithm": name,
                "review_id": int(review_id),
                "cluster_id": int(cluster_id),
            })

        # 6. Extract representative words and example review.
        for cluster_id in unique_labels:
            indices = np.flatnonzero(labels == cluster_id)

            average_tfidf = np.asarray(
                X[indices].mean(axis=0)
            ).ravel()

            top_indices = np.argsort(
                average_tfidf
            )[::-1][:8]

            keywords = feature_names[top_indices].tolist()

            center = Z[indices].mean(axis=0)
            best_local = int(
                np.argmax(Z[indices] @ center)
            )
            example = data.iloc[indices[best_local]]

            example_text = example.get(
                "review_text",
                example["text_normalized"],
            )

            topic_rows.append({
                "algorithm": name,
                "cluster_id": int(cluster_id),
                "cluster_size": len(indices),
                "label": " / ".join(keywords[:3]),
                "top_terms": " | ".join(keywords),
                "example_review_id": int(example["review_id"]),
                "example_text": str(example_text)[:350],
            })

    metrics = pd.DataFrame(metric_rows).sort_values(
        "silhouette_cosine",
        ascending=False,
        na_position="last",
    )
    topics = pd.DataFrame(topic_rows)
    assignments = pd.DataFrame(assignment_rows)

    return metrics, topics, assignments


def main():
    parser = argparse.ArgumentParser(
        description="Compare customer review clustering methods"
    )

    parser.add_argument(
        "--input",
        default=str(ROOT / "data/processed/reviews_clean.parquet"),
    )
    parser.add_argument("--k", type=int, default=12)
    parser.add_argument("--sample", type=int, default=2500)
    parser.add_argument(
        "--outdir",
        default=str(ROOT / "data/processed/cluster_evaluation"),
    )
    args = parser.parse_args()

    reviews = pd.read_parquet(args.input)

    metrics, topics, assignments = evaluate_clustering(
        reviews,
        n_clusters=args.k,
        sample_size=args.sample,
    )

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    metrics.to_csv(
        outdir / "clustering_metrics.csv", index=False
    )
    topics.to_csv(
        outdir / "cluster_topics.csv", index=False
    )
    assignments.to_csv(
        outdir / "cluster_assignments_sample.csv", index=False
    )

    print("\nCLUSTERING COMPARISON")
    print(metrics.round(4).to_string(index=False))
    print(f"\nResults saved to: {outdir}")


if __name__ == "__main__":
    main()
