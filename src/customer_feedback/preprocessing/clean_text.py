"""Text cleaning and deduplication for review data.

Input : DataFrame produced by the data_ingestion step (validated reviews).
Output: DataFrame with cleaned `summary` / `text`, duplicates removed.

Casing is deliberately preserved: embeddings and LLMs work better with natural text.
Lowercasing, stopword removal, etc. should happen later inside `text_mining/`.
"""
from __future__ import annotations

import html
import logging
import re
import unicodedata

import pandas as pd

logger = logging.getLogger(__name__)

_BR_RE = re.compile(r"<\s*br\s*/?\s*>", flags=re.IGNORECASE)
# Matches real tags only (<b>, </a>, <a href="...">), not "I paid < 5 and > 3".
_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")
_URL_RE = re.compile(r"(?:https?://|\bwww\.)\S+", flags=re.IGNORECASE)
_WS_RE = re.compile(r"\s+")
# 4+ repeated letters/!/?/. ("ewwwwww", "!!!!!!") -> 3. Digits are left alone ("100000").
_REPEAT_RE = re.compile(r"([A-Za-z!?.])\1{3,}")
_NON_ASCII_RE = r"[^\x00-\x7F]"
_QUOTES = str.maketrans(
    {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-"}
)

# Rows whose cleaned text is shorter than this are dropped.
MIN_TEXT_CHARS = 10

# A review copied across several product variants shares these three fields.
DEDUP_KEYS = ["user_id", "timestamp", "text"]


def clean_series(s: pd.Series) -> pd.Series:
    """Clean a text Series.

    Strips HTML tags, decodes entities, normalizes Unicode (NFKC) and curly quotes,
    removes URLs, shortens runs of repeated characters and collapses whitespace.
    """
    s = s.astype("string")
    s = s.str.replace(_BR_RE, " ", regex=True)
    s = s.str.replace(_TAG_RE, " ", regex=True)

    # html.unescape is slow, so only run it on rows that contain an entity.
    has_entity = s.str.contains("&", regex=False).fillna(False).to_numpy(dtype=bool)
    if has_entity.any():
        s = s.copy()
        s[has_entity] = s[has_entity].map(html.unescape)

    # Unicode: NFKC + curly quotes -> straight quotes (only rows with non-ASCII chars)
    non_ascii = s.str.contains(_NON_ASCII_RE, regex=True).fillna(False).to_numpy(dtype=bool)
    if non_ascii.any():
        s = s.copy()
        s[non_ascii] = s[non_ascii].map(lambda x: unicodedata.normalize("NFKC", x).translate(_QUOTES))

    s = s.str.replace(_URL_RE, " ", regex=True)
    # Arrow's regex engine has no backreferences, so this step runs on Python objects.
    s = s.astype(object).map(lambda x: _REPEAT_RE.sub(r"\1\1\1", x), na_action="ignore")
    s = s.astype("string")
    s = s.str.replace(_WS_RE, " ", regex=True).str.strip()
    return s


def clean_reviews(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Deduplicate and clean review text.

    Steps:
        1. Drop duplicate reviews (same user_id + timestamp + raw text), keeping the first.
        2. Clean `text` and `summary`.
        3. Drop duplicates again: reviews that differed only by HTML/whitespace now match.
        4. Drop rows whose cleaned text is shorter than MIN_TEXT_CHARS.

    Returns:
        (cleaned DataFrame, dict of row counts for logging/reporting)
    """
    stats: dict[str, int] = {"rows_in": len(df)}

    df = df.drop_duplicates(subset=DEDUP_KEYS, keep="first").copy()
    stats["dropped_duplicates"] = stats["rows_in"] - len(df)

    df["text"] = clean_series(df["text"])
    df["summary"] = clean_series(df["summary"])

    n_before = len(df)
    df = df.drop_duplicates(subset=DEDUP_KEYS, keep="first")
    stats["dropped_duplicates_after_clean"] = n_before - len(df)

    n_before = len(df)
    df = df[df["text"].str.len() >= MIN_TEXT_CHARS]
    stats["dropped_too_short"] = n_before - len(df)

    df = df.reset_index(drop=True)
    stats["rows_out"] = len(df)
    logger.info("Cleaning done: %s", stats)
    return df, stats