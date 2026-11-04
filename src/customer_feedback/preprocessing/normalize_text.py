"""Heavy normalization for classic text mining (TF-IDF, keywords, topic models).

Produces the `text_normalized` column. It is a SEPARATE column on purpose:
embeddings / RAG / LLMs should keep using the natural `review_text`.

Steps: lowercase -> expand contractions -> keep letters only -> drop stopwords
and 1-letter tokens. Negations ("not", "no", "never", ...) are KEPT because they
flip meaning ("not good"). No stemming/lemmatization (keeps results readable).
"""
from __future__ import annotations

import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

NEGATIONS = frozenset(
    {"no", "not", "nor", "never", "cannot", "without", "none", "nothing", "neither"}
)
STOPWORDS = frozenset(ENGLISH_STOP_WORDS - NEGATIONS)

# Order matters: irregular forms first, then the generic "n't" rule.
_CONTRACTIONS = [
    (r"\bcan't\b", "cannot"),
    (r"\bwon't\b", "will not"),
    (r"n't\b", " not"),
    (r"'(?:s|re|ve|ll|d|m)\b", ""),
]


def normalize_for_mining(s: pd.Series) -> pd.Series:
    """Return a lowercase, stopword-free version of `s` (space-separated tokens)."""
    s = s.astype("string").str.lower()
    for pattern, repl in _CONTRACTIONS:
        s = s.str.replace(pattern, repl, regex=True)
    s = s.str.replace(r"[^a-z\s]", " ", regex=True)

    tokens = [
        " ".join(w for w in text.split() if len(w) > 1 and w not in STOPWORDS)
        for text in s.fillna("")
    ]
    return pd.Series(tokens, index=s.index, dtype="string")