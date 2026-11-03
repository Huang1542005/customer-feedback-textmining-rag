import numpy as np
import pandas as pd

from customer_feedback.preprocessing.build_features import build_features
from customer_feedback.preprocessing.clean_text import clean_reviews, clean_series


def _df():
    return pd.DataFrame(
        {
            "review_id": [1, 2, 3, 4],
            "product_id": ["P1", "P2", "P3", "P4"],
            "user_id": ["U1", "U1", "U2", "U3"],
            "profile_name": ["a", "a", "b", "c"],
            "helpful_yes": [2, 2, 0, 1],
            "helpful_total": [4, 4, 0, 1],
            "score": [5, 5, 1, 3],
            "timestamp": [1303862400, 1303862400, 1346976000, 1219017600],
            "summary": ["Great", "Great", None, "Meh"],
            "text": [
                "Love it.<br /><br />Visit http://x.com now &amp; enjoy",
                "Love it.<br /><br />Visit http://x.com now &amp; enjoy",
                "Awful, tasted like <b>chemicals</b>, I paid < 5 and > 3",
                "short",
            ],
        }
    ).assign(review_date=lambda d: pd.to_datetime(d["timestamp"], unit="s"))


def test_clean_series():
    s = pd.Series(["a<br />b  <a href='http://x.com'>link</a> &quot;hi&quot; www.foo.com"])
    assert clean_series(s).iloc[0] == 'a b link "hi"'


def test_www_needs_word_boundary():
    out = clean_series(pd.Series(["it was ewwww. Sorry, see www.foo.com"]))
    assert out.iloc[0] == "it was ewwww. Sorry, see"


def test_dedup_after_clean():
    df = _df().iloc[[0]].copy()
    twin = df.copy()
    twin["review_id"] = 99
    twin["text"] = "Love it. Visit now & enjoy"  # differs from raw only by markup
    twin["text"] = twin["text"].str.replace("now", "http://x.com now")
    out, stats = clean_reviews(pd.concat([df, twin], ignore_index=True))
    assert stats["dropped_duplicates"] == 0
    assert stats["dropped_duplicates_after_clean"] == 1
    assert len(out) == 1


def test_clean_keeps_comparison_signs():
    out = clean_series(pd.Series(["I paid < 5 and > 3"]))
    assert out.iloc[0] == "I paid < 5 and > 3"


def test_clean_reviews_dedup_and_short():
    out, stats = clean_reviews(_df())
    assert stats["dropped_duplicates"] == 1
    assert stats["dropped_too_short"] == 1  # "short" has 5 chars
    assert list(out["review_id"]) == [1, 3]


def test_build_features():
    out, _ = clean_reviews(_df())
    out = build_features(out)
    assert out.loc[0, "review_text"].startswith("Great. Love it.")
    assert out.loc[1, "review_text"] == out.loc[1, "text"]  # null summary
    assert list(out["sentiment"].astype(str)) == ["positive", "negative"]
    assert list(out["is_negative"]) == [False, True]
    assert out.loc[0, "helpful_ratio"] == 0.5
    assert np.isnan(out.loc[1, "helpful_ratio"])
    