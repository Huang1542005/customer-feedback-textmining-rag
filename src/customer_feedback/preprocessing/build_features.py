"""Derive modeling features from cleaned reviews."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .normalize_text import normalize_for_mining

SENTIMENT_ORDER = ["negative", "neutral", "positive"]


def score_to_sentiment(score: pd.Series) -> pd.Series:
    """Map star rating to a coarse sentiment label: 1-2 negative, 3 neutral, 4-5 positive."""
    labels = np.select([score <= 2, score == 3], ["negative", "neutral"], default="positive")
    return pd.Series(
        pd.Categorical(labels, categories=SENTIMENT_ORDER), index=score.index
    )


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns (returns a new DataFrame).

    New columns:
        review_text    summary + text in one field, natural casing (embeddings, RAG, LLM, sentiment)
        text_normalized  lowercase, stopwords removed (TF-IDF, keywords, topic models)
        char_count     length of `text` in characters
        word_count     number of whitespace-separated words in `text`
        sentiment      negative / neutral / positive (from score)
        is_negative    True if score <= 2 (the subset for issue analysis)
        helpful_ratio  helpful_yes / helpful_total (NaN when nobody voted)
        review_year, review_month
    """
    out = df.copy()

    summary = out["summary"].fillna("")
    out["review_text"] = np.where(
        summary.str.len() > 0, summary + ". " + out["text"], out["text"]
    )
    out["review_text"] = out["review_text"].astype("string")

    out["text_normalized"] = normalize_for_mining(out["review_text"])

    out["char_count"] = out["text"].str.len().astype("int32")
    out["word_count"] = out["text"].str.split().str.len().astype("int32")

    out["sentiment"] = score_to_sentiment(out["score"])
    out["is_negative"] = out["score"] <= 2

    total = out["helpful_total"].replace(0, np.nan)
    out["helpful_ratio"] = (out["helpful_yes"] / total).astype("float32")

    out["review_year"] = out["review_date"].dt.year.astype("int16")
    out["review_month"] = out["review_date"].dt.month.astype("int8")
    return out