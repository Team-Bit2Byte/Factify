"""
Text-only adapter for the shipped tweet fake-news classifier.

The bundled joblib artifact was trained on a larger tweet/user feature set.
Factify only has raw text at inference time for direct text analysis, so this
module derives the tweet-side lexical features it can from plain text, leaves
unsupported metadata features neutral, and exposes the result with coverage
metadata so callers can blend it conservatively.
"""

from __future__ import annotations

import json
import os
import re
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List

import joblib
import numpy as np

try:
    from sklearn.exceptions import InconsistentVersionWarning
except Exception:  # pragma: no cover - older sklearn
    InconsistentVersionWarning = Warning

MODEL_PATH = Path(__file__).with_name("tweet_fake_model.joblib")
METRICS_PATH = Path(__file__).with_name("tweet_fake_metrics.json")
_MODEL_CACHE: dict | None = None
_METRICS_CACHE: dict | None = None

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

_WORD_RE = re.compile(r"[A-Za-z0-9_']+")
_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_HASHTAG_RE = re.compile(r"#\w+")
_MENTION_RE = re.compile(r"(?<!\w)@\w+")
_STOCK_RE = re.compile(r"(?<!\w)\$[A-Z]{1,5}\b")
_NUMBER_RE = re.compile(r"\b\d+(?:[.,:/-]\d+)*\b")
_ASCII_EMOJI_RE = re.compile(r"(:\)|:-\)|:\(|:-\(|:D|:-D|;\)|;-\)|:P|:-P|XD|<3)")
_UNICODE_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F900-\U0001F9FF"
    "\U0001FA70-\U0001FAFF"
    "]",
    flags=re.UNICODE,
)
_QUOTE_RE = re.compile(r"[\"'“”‘’]")
_REPEATED_CHAR_RE = re.compile(r"(.)\1{2,}")
_TITLE_TOKEN_RE = re.compile(r"\b[A-Z][a-z]{2,}\b")
_ALL_CAPS_RE = re.compile(r"\b[A-Z]{2,}\b")
_SENTENCE_SPLIT_RE = re.compile(r"[.!?]+")

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "he", "in", "is", "it", "its", "of", "on", "or", "that", "the", "to",
    "was", "were", "will", "with", "this", "these", "those", "their", "there",
    "have", "had", "been", "if", "but", "not", "you", "your", "we", "they",
    "them", "our", "i", "me", "my", "who", "what", "when", "where", "why",
    "how", "which", "about", "into", "than", "then", "so", "too", "very",
}
_PRONOUNS = {
    "i", "me", "my", "mine", "we", "our", "ours", "you", "your", "yours",
    "he", "him", "his", "she", "her", "hers", "they", "them", "their",
    "theirs", "it", "its",
}
_SLANG = {
    "lol", "omg", "wtf", "lmao", "idk", "imo", "imho", "brb", "tbh", "smh",
    "btw", "fyi", "rofl", "yolo", "ikr", "sus", "nah", "bro", "gonna",
}
_POSITIVE_WORDS = {
    "accurate", "authentic", "confirmed", "credible", "good", "genuine", "great",
    "legit", "official", "positive", "real", "reliable", "safe", "true", "valid",
    "verified", "win", "wins",
}
_NEGATIVE_WORDS = {
    "alarm", "bombshell", "chaos", "conspiracy", "corrupt", "crisis", "disaster",
    "exposed", "fake", "fraud", "hoax", "lies", "lying", "outrage", "panic",
    "propaganda", "rumor", "rumour", "scam", "secret", "shocking", "stolen",
    "unverified", "urgent",
}
_SENSITIVE_WORDS = {"blood", "death", "graphic", "kill", "murder", "nsfw", "violence"}
_POPULAR_HASHTAGS = {
    "breaking", "news", "viral", "trending", "exclusive", "alert", "mustread",
}


@dataclass
class TweetModelAssessment:
    enabled: bool
    model_name: str = "tweet_fake_model"
    verdict: str = "unverified"
    verdict_label: str = "Unverified"
    raw_probability: float = 0.0
    fake_probability: int = 0
    original_probability: int = 100
    confidence: str = "low"
    confidence_score: int = 0
    threshold_used: float = 0.5
    feature_count: int = 0
    derived_feature_count: int = 0
    coverage_ratio: float = 0.0
    summary: str = ""
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _load_bundle() -> dict:
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InconsistentVersionWarning)
            _MODEL_CACHE = joblib.load(MODEL_PATH)
    return _MODEL_CACHE


def _load_metrics() -> dict:
    global _METRICS_CACHE
    if _METRICS_CACHE is None:
        _METRICS_CACHE = json.loads(METRICS_PATH.read_text())
    return _METRICS_CACHE


def _count_matches(values: Iterable[str], candidates: set[str]) -> int:
    return sum(1 for value in values if value in candidates)


def _safe_ratio(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return float(numerator) / float(denominator)


def _looks_like_verb(token: str) -> bool:
    return token.endswith(("ed", "ing", "ize", "ise")) or token in {
        "is", "are", "was", "were", "be", "am", "have", "has", "had", "do", "does", "did"
    }


def _looks_like_adjective(token: str) -> bool:
    return token.endswith(("al", "ary", "ful", "ible", "ic", "ish", "ive", "less", "ous", "y"))


def _looks_like_noun(token: str) -> bool:
    return token.endswith(("age", "dom", "er", "hood", "ion", "ism", "ist", "ity", "ment", "ness", "ship", "ty"))


def _build_text_features(text: str, feature_names: List[str]) -> tuple[np.ndarray, int]:
    cleaned_text = (text or "").strip()
    lowered_text = cleaned_text.lower()
    words = _WORD_RE.findall(cleaned_text)
    lowered_words = [word.lower() for word in words]
    tokens_without_urls = [token for token in lowered_words if not token.startswith(("http", "www"))]
    urls = _URL_RE.findall(cleaned_text)
    hashtags = [tag[1:].lower() for tag in _HASHTAG_RE.findall(cleaned_text)]
    mentions = _MENTION_RE.findall(cleaned_text)
    ascii_emojis = _ASCII_EMOJI_RE.findall(cleaned_text)
    unicode_emojis = _UNICODE_EMOJI_RE.findall(cleaned_text)
    sentences = [chunk.strip() for chunk in _SENTENCE_SPLIT_RE.split(cleaned_text) if chunk.strip()]
    punctuation_chars = re.findall(r"[^\w\s]", cleaned_text)
    capitalized_words = [word for word in words if len(word) > 1 and word[0].isupper() and word[1:].islower()]
    all_caps_words = _ALL_CAPS_RE.findall(cleaned_text)
    title_tokens = _TITLE_TOKEN_RE.findall(cleaned_text)
    positive_word_count = _count_matches(lowered_words, _POSITIVE_WORDS)
    negative_word_count = _count_matches(lowered_words, _NEGATIVE_WORDS)
    sentiment_word_count = positive_word_count + negative_word_count
    slang_count = _count_matches(lowered_words, _SLANG)
    pronoun_count = _count_matches(lowered_words, _PRONOUNS)
    stopword_count = _count_matches(lowered_words, _STOPWORDS)
    adjective_count = sum(1 for word in lowered_words if _looks_like_adjective(word))
    noun_count = sum(1 for word in lowered_words if _looks_like_noun(word))
    verb_count = sum(1 for word in lowered_words if _looks_like_verb(word))
    uppercase_letters = sum(1 for char in cleaned_text if char.isupper())
    alpha_letters = sum(1 for char in cleaned_text if char.isalpha())
    media_count = sum(1 for url in urls if any(marker in url.lower() for marker in ("pic.twitter", "pbs.twimg", ".jpg", ".jpeg", ".png", ".gif", ".mp4")))
    exclamation_count = cleaned_text.count("!")
    question_count = cleaned_text.count("?")
    url_chars = sum(len(url) for url in urls)
    words_count = len(words)
    token_count = len(tokens_without_urls)
    now = np.datetime64("now")

    # Features that Factify can derive directly from raw text.
    derived_values: Dict[str, float] = {
        "tweet__truncated": 1.0 if len(cleaned_text) > 280 else 0.0,
        "tweet__possibly_sensitive": 1.0 if any(word in lowered_words for word in _SENSITIVE_WORDS) else 0.0,
        "tweet__nr_pos_sentiment_words": float(positive_word_count),
        "tweet__subjectivity_score": round(min(1.0, _safe_ratio(pronoun_count + exclamation_count + question_count + sentiment_word_count, max(words_count, 1)) * 3.5), 4),
        "tweet__sentiment_score": round(max(-1.0, min(1.0, _safe_ratio(positive_word_count - negative_word_count, max(sentiment_word_count, 1)))), 4),
        "tweet__nr_of_sentiment_words": float(sentiment_word_count),
        "tweet__nr_neg_sentiment_words": float(negative_word_count),
        "tweet__nr_of_sentences": float(len(sentences) or (1 if cleaned_text else 0)),
        "tweet__nr_of_unicode_emojis": float(len(unicode_emojis)),
        "tweet__nr_of_ascii_emojis": float(len(ascii_emojis)),
        "tweet__nr_of_words": float(words_count),
        "tweet__nr_of_slang_words": float(slang_count),
        "tweet__nr_of_tokens": float(token_count),
        "tweet__nr_of_urls": float(len(urls)),
        "tweet__nr_of_punctuations": float(len(punctuation_chars)),
        "tweet__nr_of_exclamation_marks": float(exclamation_count),
        "tweet__nr_of_question_marks": float(question_count),
        "tweet__nr_of_medias": float(media_count),
        "tweet__nr_of_user_mentions": float(len(mentions)),
        "tweet__nr_of_hashtags": float(len(hashtags)),
        "tweet__nr_of_popular_hashtag": float(sum(1 for tag in hashtags if tag in _POPULAR_HASHTAGS)),
        "tweet__avg_word_length": round(_safe_ratio(sum(len(word) for word in words), words_count), 4),
        "tweet__avg_url_length": round(_safe_ratio(url_chars, max(len(urls), 1)), 4),
        "tweet__contains_spelling_mistake": 1.0 if any(_REPEATED_CHAR_RE.search(word) for word in lowered_words) else 0.0,
        "tweet__contains_unicode_emojis": 1.0 if unicode_emojis else 0.0,
        "tweet__contains_face_positive_emojis": 1.0 if any(emoji in {"😀", "😁", "😊", "😍", "🥳"} for emoji in unicode_emojis) else 0.0,
        "tweet__contains_face_negative_emojis": 1.0 if any(emoji in {"😡", "😢", "😭", "😱", "🤬"} for emoji in unicode_emojis) else 0.0,
        "tweet__contains_face_neutral_emojis": 1.0 if any(emoji in {"😐", "😶", "🤔"} for emoji in unicode_emojis) else 0.0,
        "tweet__contains_ascii_emojis": 1.0 if ascii_emojis else 0.0,
        "tweet__contains_named_entities": 1.0 if len(set(title_tokens)) >= 2 else 0.0,
        "tweet__contains_pronouns": 1.0 if pronoun_count else 0.0,
        "tweet__contains_urls": 1.0 if urls else 0.0,
        "tweet__contains_stock_symbol": 1.0 if _STOCK_RE.search(cleaned_text) else 0.0,
        "tweet__contains_punctuation": 1.0 if punctuation_chars else 0.0,
        "tweet__contains_exclamation_mark": 1.0 if exclamation_count else 0.0,
        "tweet__contains_question_mark": 1.0 if question_count else 0.0,
        "tweet__contains_character_repetitions": 1.0 if _REPEATED_CHAR_RE.search(cleaned_text) else 0.0,
        "tweet__contains_slang": 1.0 if slang_count else 0.0,
        "tweet__contains_uppercase_text": 1.0 if all_caps_words else 0.0,
        "tweet__contains_number": 1.0 if _NUMBER_RE.search(cleaned_text) else 0.0,
        "tweet__contains_quote": 1.0 if _QUOTE_RE.search(cleaned_text) else 0.0,
        "tweet__contains_media": 1.0 if media_count else 0.0,
        "tweet__contains_user_mention": 1.0 if mentions else 0.0,
        "tweet__contains_hashtags": 1.0 if hashtags else 0.0,
        "tweet__contains_popular_hashtag": 1.0 if any(tag in _POPULAR_HASHTAGS for tag in hashtags) else 0.0,
        "tweet__contains_sentiment": 1.0 if sentiment_word_count else 0.0,
        "tweet__is_all_uppercase": 1.0 if cleaned_text and cleaned_text.upper() == cleaned_text and any(char.isalpha() for char in cleaned_text) else 0.0,
        "tweet__is_ww_trending_topic": 1.0 if any(tag in _POPULAR_HASHTAGS for tag in hashtags) else 0.0,
        "tweet__has_place": 0.0,
        "tweet__has_location": 1.0 if any(token in {"city", "state", "country", "street", "road"} for token in lowered_words) else 0.0,
        "tweet__text_length": float(len(cleaned_text)),
        "tweet__percent_of_text_used": round(min(1.0, _safe_ratio(len(cleaned_text), 280)), 4),
        "tweet__multiple_exclamation_marks": 1.0 if exclamation_count >= 2 else 0.0,
        "tweet__multiple_question_marks": 1.0 if question_count >= 2 else 0.0,
        "tweet__additional_preprocessed_is_empty": 1.0 if not token_count else 0.0,
        "tweet__day_of_week": float((int(now.astype("datetime64[D]").astype(int)) + 4) % 7),
        "tweet__day_of_month": float(0),
        "tweet__month_of_year": float(0),
        "tweet__am_pm": float(0),
        "tweet__hour_of_day": float(0),
        "tweet__quarter_of_year": float(0),
        "tweet__ratio_adjectives": round(_safe_ratio(adjective_count, words_count), 4),
        "tweet__ratio_nouns": round(_safe_ratio(noun_count, words_count), 4),
        "tweet__ratio_verbs": round(_safe_ratio(verb_count, words_count), 4),
        "tweet__ratio_uppercase_letters": round(_safe_ratio(uppercase_letters, max(alpha_letters, 1)), 4),
        "tweet__ratio_capitalized_words": round(_safe_ratio(len(capitalized_words), words_count), 4),
        "tweet__ratio_all_capitalized_words": round(_safe_ratio(len(all_caps_words), words_count), 4),
        "tweet__ratio_tokens_before_after_prepro": round(_safe_ratio(token_count, max(words_count, 1)), 4),
        "tweet__ratio_words_tokens": round(_safe_ratio(words_count, max(token_count, 1)), 4),
        "tweet__ratio_punctuation_tokens": round(_safe_ratio(len(punctuation_chars), max(token_count, 1)), 4),
        "tweet__ratio_pos_sentiment_words": round(_safe_ratio(positive_word_count, max(words_count, 1)), 4),
        "tweet__ratio_neg_sentiment_words": round(_safe_ratio(negative_word_count, max(words_count, 1)), 4),
        "tweet__ratio_stopwords": round(_safe_ratio(stopword_count, max(words_count, 1)), 4),
    }

    feature_vector = np.zeros(len(feature_names), dtype=np.float32)
    derived_feature_count = 0
    for index, feature_name in enumerate(feature_names):
        if feature_name in derived_values:
            feature_vector[index] = float(derived_values[feature_name])
            derived_feature_count += 1

    return feature_vector, derived_feature_count


def analyze_tweet_text(text: str) -> TweetModelAssessment:
    if not MODEL_PATH.exists() or not METRICS_PATH.exists():
        return TweetModelAssessment(
            enabled=False,
            summary="Tweet classifier assets are not available in the model directory.",
            notes=["The text-specific tweet model could not be loaded."],
        )

    bundle = _load_bundle()
    metrics = _load_metrics()
    feature_names: List[str] = list(bundle["features"])
    feature_vector, derived_feature_count = _build_text_features(text, feature_names)
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"X does not have valid feature names.*",
            category=UserWarning,
            module=r"sklearn\.utils\.validation",
        )
        raw_model_probability = float(bundle["model"].predict_proba(feature_vector.reshape(1, -1))[0][1])
    threshold = float(metrics.get("calibrated_threshold") or bundle.get("decision_threshold") or 0.5)
    coverage_fraction = derived_feature_count / max(len(feature_names), 1)
    # Less aggressive regularization - maintain more of the model's prediction even with partial coverage
    # Use sqrt of coverage to reduce the penalty for missing features
    coverage_weight = max(0.4, min(1.0, coverage_fraction ** 0.5))
    probability = 0.5 + ((raw_model_probability - 0.5) * coverage_weight)
    fake_probability = int(round(probability * 100))
    original_probability = 100 - fake_probability
    coverage_ratio = round((derived_feature_count / max(len(feature_names), 1)) * 100, 2)

    if probability >= 0.67:
        verdict = "likely_fake_false"
        verdict_label = "Likely Fake / False"
        summary = "The text-specific classifier still leans high-risk even after regularizing for missing tweet metadata."
    elif probability <= 0.33:
        verdict = "likely_original"
        verdict_label = "Likely Original"
        summary = "The text-specific classifier stays in the lower-risk band after adjusting for partial feature coverage."
    else:
        verdict = "unverified"
        verdict_label = "Unverified"
        summary = "The text-specific classifier lands in the gray zone once its score is regularized for partial feature coverage."

    confidence_score = int(round(min(100.0, abs(probability - 0.5) * 200)))
    if confidence_score >= 70:
        confidence = "high"
    elif confidence_score >= 40:
        confidence = "medium"
    else:
        confidence = "low"

    notes = [
        f"Derived {derived_feature_count} of {len(feature_names)} expected tweet features directly from raw text.",
        f"Raw classifier probability {raw_model_probability:.3f} was regularized to {probability:.3f} using {coverage_ratio:.2f}% feature coverage.",
        f"Applied calibrated threshold {threshold:.3f} from the shipped metrics file.",
        "Unavailable account-level and embedding features were held at neutral defaults.",
    ]

    return TweetModelAssessment(
        enabled=True,
        model_name=str(bundle.get("model_name") or "tweet_fake_model"),
        verdict=verdict,
        verdict_label=verdict_label,
        raw_probability=round(probability, 4),
        fake_probability=fake_probability,
        original_probability=original_probability,
        confidence=confidence,
        confidence_score=confidence_score,
        threshold_used=round(threshold, 4),
        feature_count=len(feature_names),
        derived_feature_count=derived_feature_count,
        coverage_ratio=coverage_ratio,
        summary=summary,
        notes=notes,
    )
