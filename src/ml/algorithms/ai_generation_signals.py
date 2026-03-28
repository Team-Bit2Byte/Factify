"""
Heuristic AI-writing signals used as one component of fake-news scoring.

This is not an authorship detector. It scores how strongly the text resembles
overly regular, templated, weakly grounded generated-news prose.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, asdict
from statistics import pstdev
from typing import List

_SENTENCE_SPLIT_RE = re.compile(r"[.!?]+")
_WORD_RE = re.compile(r"[a-z0-9']+")
_TRANSITIONS = [
    "moreover", "furthermore", "additionally", "however", "therefore", "meanwhile",
    "notably", "overall", "in conclusion", "in summary", "on the other hand",
]
_HEDGES = [
    "could", "may", "might", "appears to", "suggests that", "reportedly", "seems to",
    "is believed to", "potentially", "arguably",
]
_TEMPLATED_PHRASES = [
    "in a surprising turn of events", "has sparked widespread debate", "supporters argue",
    "critics argue", "raises important questions", "in today's world", "it is worth noting",
    "plays a crucial role", "is likely to continue", "remains to be seen",
]
_GROUNDING_MARKERS = [
    "according to", "official statement", "court", "ministry", "agency", "committee",
    "data shows", "study found", "audit", "filing", "reuters", "bbc", "associated press",
]


@dataclass
class AiWritingAssessment:
    score: float
    flags: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


def assess_ai_writing_signals(headline: str, body: str) -> AiWritingAssessment:
    normalized_headline = (headline or "").strip().lower()
    normalized_body = (body or "").strip().lower()
    if normalized_headline and normalized_headline == normalized_body:
        text = normalized_body
    elif normalized_headline and normalized_body and normalized_headline in normalized_body:
        text = normalized_body
    else:
        text = f"{normalized_headline} {normalized_body}".strip()
    sentences = [segment.strip() for segment in _SENTENCE_SPLIT_RE.split(text) if segment.strip()]
    words = _WORD_RE.findall(text)
    word_count = len(words)

    if word_count < 20:
        return AiWritingAssessment(score=55.0, flags=[])

    sentence_lengths = [len(_WORD_RE.findall(sentence)) for sentence in sentences if sentence]
    avg_sentence_len = (sum(sentence_lengths) / len(sentence_lengths)) if sentence_lengths else 0.0
    sentence_len_std = pstdev(sentence_lengths) if len(sentence_lengths) > 1 else 0.0
    lexical_diversity = len(set(words)) / max(word_count, 1)
    transition_hits = sum(text.count(marker) for marker in _TRANSITIONS)
    hedge_hits = sum(text.count(marker) for marker in _HEDGES)
    templated_hits = sum(text.count(marker) for marker in _TEMPLATED_PHRASES)
    grounding_hits = sum(text.count(marker) for marker in _GROUNDING_MARKERS)

    punctuation_total = sum(text.count(mark) for mark in ",;:")
    punctuation_ratio = punctuation_total / max(word_count, 1)
    repeated_bigrams = 0
    if word_count >= 8:
        bigrams = [" ".join(words[index:index + 2]) for index in range(len(words) - 1)]
        repeated_bigrams = len(bigrams) - len(set(bigrams))

    risk = 0.0
    flags: List[str] = []

    if avg_sentence_len >= 18:
        risk += min(14.0, (avg_sentence_len - 17.0) * 1.4)
        flags.append("Long, polished sentence structure")
    if len(sentence_lengths) >= 3 and sentence_len_std <= 3.2:
        risk += 12.0
        flags.append("Unusually uniform sentence lengths")
    if lexical_diversity <= 0.52:
        risk += 14.0
        flags.append("Low lexical diversity")
    if transition_hits >= 2:
        risk += min(12.0, transition_hits * 4.0)
        flags.append("Heavy use of connective transitions")
    if hedge_hits >= 2:
        risk += min(10.0, hedge_hits * 3.0)
        flags.append("Frequent hedging language")
    if templated_hits >= 1:
        risk += min(18.0, 8.0 + templated_hits * 5.0)
        flags.append("Template-like narrative phrasing")
    if punctuation_ratio >= 0.11:
        risk += 6.0
        flags.append("Over-structured punctuation pattern")
    if repeated_bigrams >= 2:
        risk += min(10.0, repeated_bigrams * 2.5)
        flags.append("Repeated phrase construction")
    if grounding_hits >= 2:
        risk -= min(14.0, grounding_hits * 4.0)
    if any(char.isdigit() for char in text):
        risk -= 3.0

    score = max(0.0, min(100.0, 62.0 - risk + min(10.0, grounding_hits * 2.0)))
    return AiWritingAssessment(score=round(score, 2), flags=list(dict.fromkeys(flags))[:4])
