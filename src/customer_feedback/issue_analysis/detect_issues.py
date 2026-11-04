"""Detect recurring complaint themes ("issues") in negative reviews.

Pipeline
    complaints (score <= max_score)
      -> issue-oriented vocabulary (terms skewed towards complaints, filler removed)
      -> TF-IDF
      -> NMF topic model (default) or KMeans
      -> one issue per complaint

Why a custom vocabulary? Plain topic models on negative reviews mostly recover
*product categories* (coffee, tea, dog food) because those words are frequent.
Words such as "coffee" appear just as often in 5-star reviews, so contrasting
complaints against positive reviews (log-odds) removes them and keeps the
words that describe what went wrong (stale, broken, overpriced, ...).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import NMF, TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize

logger = logging.getLogger(__name__)

# Words that carry no information about WHAT went wrong. A vocabulary term is
# dropped when ALL of its tokens are filler or negations ("did not", "never buy").
FILLER_TERMS = frozenset(
    {
        "bought", "thought", "got", "know", "maybe", "product", "products", "purchased",
        "tried", "think", "did", "does", "just", "really", "like", "want", "wanted",
        "made", "make", "use", "used", "going", "said", "say", "get", "buy", "guess",
        "review", "reviews", "read", "sure", "one", "bit", "little", "much", "even",
        "also", "still", "way", "thing", "things", "time", "times", "good", "bad",
    }
)
_NEGATIONS = frozenset({"no", "not", "nor", "never", "cannot", "without", "none", "nothing", "neither"})
# Pure sentiment phrases: they say the customer is unhappy, not why.
GENERIC_PHRASES = frozenset(
    {
        "not good", "disappointed", "really disappointed", "extremely disappointed",
        "disappointed not", "not recommend", "terrible", "awful", "horrible", "worst",
        "not like", "just not", "definitely not", "really bad", "not worth", "not buy",
        "not purchase", "not great",
    }
)


@dataclass
class IssueConfig:
    n_issues: int = 12            # number of issue groups to discover
    method: str = "nmf"           # "nmf" (topic model) or "kmeans" (clustering)
    max_score: int = 2            # reviews with score <= max_score are complaints
    min_df: int = 20              # a term must appear in >= min_df complaints
    min_log_odds: float = 0.3     # complaint-vs-positive skew required to keep a term
    max_features: int = 60_000    # cap for the candidate vocabulary
    reference_sample: int = 100_000  # positive reviews used as the contrast set
    top_terms: int = 10
    random_state: int = 42


@dataclass
class IssueResult:
    assignments: pd.DataFrame  # review_id, issue_id, issue_strength (-1 = no signal; higher strength = clearer example)
    issues: pd.DataFrame       # issue_id, label, top_terms
    X: object                  # TF-IDF matrix of the rows used for fitting
    fitted_mask: np.ndarray    # which complaints were used for fitting
    labels: np.ndarray         # issue id of each fitted row
    config: IssueConfig


def _is_filler(term: str) -> bool:
    return all(tok in FILLER_TERMS or tok in _NEGATIONS for tok in term.split())


def build_issue_vocabulary(
    complaints: pd.Series, reference: pd.Series, cfg: IssueConfig
) -> list[str]:
    """Terms (uni/bigrams) that are noticeably more common in complaints than in positive reviews."""
    texts = pd.concat([complaints, reference], ignore_index=True)
    cv = CountVectorizer(
        ngram_range=(1, 2), min_df=cfg.min_df, max_df=0.3, binary=True,
        max_features=cfg.max_features,
    )
    counts = cv.fit_transform(texts)
    terms = np.array(cv.get_feature_names_out())

    n_c = len(complaints)
    df_c = np.asarray(counts[:n_c].sum(axis=0)).ravel()
    df_p = np.asarray(counts[n_c:].sum(axis=0)).ravel()
    log_odds = np.log(((df_c + 1) / (n_c + 2)) / ((df_p + 1) / (len(reference) + 2)))

    keep = (log_odds >= cfg.min_log_odds) & (df_c >= cfg.min_df)
    vocab = [
        t for t, k in zip(terms, keep)
        if k and t not in GENERIC_PHRASES and not _is_filler(t)
    ]
    logger.info("Issue vocabulary: %d terms (from %d candidates)", len(vocab), len(terms))
    return vocab


def _fit_nmf(X, cfg: IssueConfig):
    model = NMF(n_components=cfg.n_issues, init="nndsvd", random_state=cfg.random_state, max_iter=300)
    W = model.fit_transform(X)
    labels = W.argmax(axis=1)
    strength = W.max(axis=1)  # how strongly the review expresses its main issue
    return labels, strength, model.components_


def _fit_kmeans(X, cfg: IssueConfig):
    n_comp = min(100, X.shape[1] - 1)
    Z = normalize(TruncatedSVD(n_components=n_comp, random_state=cfg.random_state).fit_transform(X))
    km = MiniBatchKMeans(
        n_clusters=cfg.n_issues, random_state=cfg.random_state, n_init=5, batch_size=2048
    )
    labels = km.fit_predict(Z)
    strength = (Z * normalize(km.cluster_centers_)[labels]).sum(axis=1)  # cosine to centroid
    term_weights = np.vstack(
        [np.asarray(X[labels == i].mean(axis=0)).ravel() for i in range(cfg.n_issues)]
    )
    return labels, strength, term_weights


def detect_issues(df: pd.DataFrame, cfg: IssueConfig | None = None) -> IssueResult:
    """Group complaint reviews into issues.

    Args:
        df: preprocessed reviews (needs review_id, score, text_normalized).
        cfg: IssueConfig (defaults are tuned for Amazon Fine Food Reviews).
    """
    cfg = cfg or IssueConfig()
    if cfg.method not in {"nmf", "kmeans"}:
        raise ValueError("method must be 'nmf' or 'kmeans'")

    has_text = df["text_normalized"].fillna("").str.len() > 0
    complaints = df[has_text & (df["score"] <= cfg.max_score)].reset_index(drop=True)
    reference = df.loc[has_text & (df["score"] >= 4), "text_normalized"]
    if len(reference) > cfg.reference_sample:
        reference = reference.sample(cfg.reference_sample, random_state=cfg.random_state)
    logger.info("Complaints: %d | reference positives: %d", len(complaints), len(reference))

    vocab = build_issue_vocabulary(complaints["text_normalized"], reference, cfg)
    vec = TfidfVectorizer(vocabulary=vocab, ngram_range=(1, 2), sublinear_tf=True)
    X_all = vec.fit_transform(complaints["text_normalized"])

    fitted = X_all.getnnz(axis=1) > 0  # rows with no issue-vocabulary term carry no signal
    X = X_all[fitted]
    labels, strength, term_weights = (_fit_nmf if cfg.method == "nmf" else _fit_kmeans)(X, cfg)

    # Renumber so that issue 0 is the largest group (stable, readable ids).
    order = np.argsort(-np.bincount(labels, minlength=cfg.n_issues))
    remap = np.empty(cfg.n_issues, dtype=int)
    remap[order] = np.arange(cfg.n_issues)
    labels = remap[labels]
    term_weights = term_weights[order]

    feature_names = np.array(vec.get_feature_names_out())
    rows = []
    for i in range(cfg.n_issues):
        top = feature_names[term_weights[i].argsort()[::-1][: cfg.top_terms]].tolist()
        rows.append({"issue_id": i, "label": " / ".join(top[:3]), "top_terms": top})
    issues = pd.DataFrame(rows)

    issue_id = np.full(len(complaints), -1, dtype=int)
    issue_strength = np.zeros(len(complaints), dtype="float32")
    issue_id[fitted] = labels
    issue_strength[fitted] = strength
    assignments = pd.DataFrame(
        {"review_id": complaints["review_id"].to_numpy(), "issue_id": issue_id,
         "issue_strength": issue_strength}
    )
    return IssueResult(assignments, issues, X, fitted, labels, cfg)


def evaluate_issues(result: IssueResult, sample: int = 5000, random_state: int = 42) -> dict:
    """Method-agnostic quality metrics, so NMF and KMeans can be compared fairly.

    silhouette_cosine: cohesion/separation in a 50-d SVD space (higher is better; text
        data is high-dimensional so values near 0.0x are normal).
    size_balance: normalized entropy of group sizes (1 = equal sizes, 0 = one giant group).
    """
    X, labels = result.X, result.labels
    k = int(result.config.n_issues)
    Z = normalize(
        TruncatedSVD(n_components=min(50, X.shape[1] - 1), random_state=random_state).fit_transform(X)
    )
    rng = np.random.default_rng(random_state)
    idx = rng.choice(len(labels), size=min(sample, len(labels)), replace=False)
    sil = silhouette_score(Z[idx], labels[idx], metric="cosine") if len(set(labels[idx])) > 1 else 0.0
    p = np.bincount(labels, minlength=k) / len(labels)
    p = p[p > 0]
    balance = float(-(p * np.log(p)).sum() / np.log(k)) if k > 1 else 1.0
    return {"method": result.config.method, "n_issues": k,
            "silhouette_cosine": round(float(sil), 4), "size_balance": round(balance, 3)}