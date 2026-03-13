"""
ml/sentiment.py
═══════════════════════════════════════════════════════════════
Lexicon-based sentiment analyser for customer reviews.

No external NLP model required — uses a curated word list.
Handles negation ("not good" → negative), intensifiers ("very good" → stronger),
and produces a score 0.0 (very negative) → 1.0 (very positive).
"""
from __future__ import annotations
import re
from typing import Tuple

# ── Sentiment lexicons ────────────────────────────────────────

POSITIVE_WORDS = {
    "amazing", "awesome", "excellent", "great", "fantastic", "wonderful",
    "delicious", "perfect", "outstanding", "superb", "brilliant", "fabulous",
    "love", "loved", "best", "fresh", "tasty", "yummy", "crispy", "tender",
    "good", "nice", "pleasant", "happy", "satisfied", "recommend", "fast",
    "quick", "friendly", "warm", "cozy", "comfortable", "clean", "beautiful",
    "helpful", "attentive", "polite", "professional", "worth", "value",
    "hot", "rich", "smooth", "creamy", "flavourful", "flavorful",
}

NEGATIVE_WORDS = {
    "terrible", "awful", "horrible", "disgusting", "worst", "bad", "poor",
    "cold", "soggy", "stale", "bland", "tasteless", "overpriced", "expensive",
    "slow", "late", "rude", "unfriendly", "dirty", "messy", "noisy",
    "disappointing", "disappointed", "wrong", "incorrect", "missing",
    "never", "waste", "overcooked", "undercooked", "raw", "burnt",
    "salty", "bitter", "dry", "hard", "tough", "small", "tiny",
}

NEGATION_WORDS = {"not", "no", "never", "n't", "neither", "nor", "barely", "hardly"}
INTENSIFIERS   = {"very", "really", "extremely", "absolutely", "so", "quite", "incredibly", "super"}
DIMINISHERS    = {"slightly", "somewhat", "a bit", "a little", "kind of", "sort of"}


def tokenise(text: str) -> list:
    return re.findall(r"\b\w+\b", text.lower())


def analyse_sentiment(text: str) -> Tuple[str, float]:
    """
    Analyse review text.

    Returns:
        (label, score)  where label in {"positive","neutral","negative"}
        and score in [0.0, 1.0]  (0=very negative, 0.5=neutral, 1=very positive)
    """
    if not text or not text.strip():
        return ("neutral", 0.5)

    tokens = tokenise(text)
    score  = 0.0
    n      = len(tokens)

    for i, token in enumerate(tokens):
        # Check 2-token lookback for negation
        negated = any(tokens[max(0, i-j)] in NEGATION_WORDS for j in range(1, 4))

        if token in POSITIVE_WORDS:
            val = 1.0
            # Intensifier before this token?
            if i > 0 and tokens[i-1] in INTENSIFIERS:
                val = 1.5
            elif i > 0 and tokens[i-1] in DIMINISHERS:
                val = 0.5
            score += -val if negated else val

        elif token in NEGATIVE_WORDS:
            val = -1.0
            if i > 0 and tokens[i-1] in INTENSIFIERS:
                val = -1.5
            elif i > 0 and tokens[i-1] in DIMINISHERS:
                val = -0.5
            score += val if negated else val

    # Normalise to [0, 1]
    if n == 0:
        return ("neutral", 0.5)

    # Cap raw score
    raw_capped = max(-5, min(5, score))
    normalised = (raw_capped + 5) / 10  # maps -5..5 → 0..1

    # Label
    if normalised >= 0.62:
        label = "positive"
    elif normalised <= 0.38:
        label = "negative"
    else:
        label = "neutral"

    return (label, round(normalised, 3))


def batch_analyse(reviews: list) -> list:
    """
    Batch sentiment analysis.
    Input:  list of {"id": ..., "comment": str, ...}
    Output: same list with sentiment and sentiment_score fields populated.
    """
    results = []
    for review in reviews:
        label, score = analyse_sentiment(review.get("comment", ""))
        results.append({**review, "sentiment": label, "sentiment_score": score})
    return results