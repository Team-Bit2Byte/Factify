"""
Deterministic credibility scoring for Factify.
"""

from __future__ import annotations

import csv
import json
import math
import re
import subprocess
from collections import Counter, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "vendor" / "factify_engine" / "data"
SOURCE_FILE = DATA_DIR / "sources.csv"
NEGATIVE_TERMS_FILE = DATA_DIR / "negative_terms.csv"
SUSPICIOUS_PHRASES_FILE = DATA_DIR / "suspicious_phrases.txt"
TEMPORAL_HISTORY_FILE = Path("/tmp/factify_temporal_history.json")
BRIDGE_BINARY = PROJECT_ROOT / "build" / "factify_credibility_bridge"
BRIDGE_BUILD_SCRIPT = PROJECT_ROOT / "scripts" / "build_credibility_bridge.sh"
TEMPORAL_WINDOW_HOURS = 24

BASE_SCORE = 85.0
BASELINE_PREPROCESSING_SCORE = 70.0
SHORT_TEXT_THRESHOLD_CRITICAL = 5
SHORT_TEXT_THRESHOLD_WARNING = 12
SHORT_TEXT_PENALTY_CRITICAL = 7.0
SHORT_TEXT_PENALTY_WARNING = 2.5
FACTUAL_CUE_BONUS = 3.5
UNCERTAINTY_PENALTY = 4.5
PHRASE_PENALTY_PER_HIT = 9.0
KMP_PENALTY_PER_HIT = 6.5
RABIN_KARP_PENALTY_PER_HIT = 4.5
FREQUENCY_PENALTY_MULTIPLIER = 0.50
MAX_PHRASE_PENALTY = 27.0
MAX_KMP_PENALTY = 26.0
MAX_RABIN_KARP_PENALTY = 18.0
MAX_FREQUENCY_PENALTY = 32.0
VERY_LOW_SOURCE_THRESHOLD = 20.0
LOW_SOURCE_CREDIBILITY_THRESHOLD = 35.0
MEDIUM_SOURCE_CREDIBILITY_THRESHOLD = 50.0
HIGH_SOURCE_THRESHOLD = 75.0
LOW_CLAIM_VERIFIABILITY_THRESHOLD = 40.0
MANIPULATION_THRESHOLD = 25.0
SUSPICION_THRESHOLD = 60.0
RISK_PENALTY_VERY_LOW_SOURCE = 8.0
RISK_PENALTY_LOW_SOURCE = 4.0
RISK_PENALTY_LOW_CLAIM_AND_SOURCE = 3.5
RISK_PENALTY_SUSPICIOUS_PATTERNS = 6.0
RISK_PENALTY_PER_UNCERTAINTY = 2.0
RISK_PENALTY_MAX_UNCERTAINTY = 7.0
RISK_PENALTY_CLAIM_MULTIPLIER = 0.40
RISK_PENALTY_COMBINED_LOW = 4.0
CONSISTENCY_BOOST_FACTUAL = 3.5
CONSISTENCY_BOOST_HIGH_CLAIM = 1.5
CONSISTENCY_BOOST_CLEAN_RECORD = 2.5
CONSISTENCY_BOOST_TRUSTED_SOURCE = 2.0
MAX_CONSISTENCY_BOOST = 7.0
SOURCE_WEIGHT = 0.36
CLAIM_WEIGHT = 0.30
PREPROCESSING_WEIGHT = 0.17
DETECTION_WEIGHT = 0.17
RISK_ADJUSTMENT_CENTER = 75.0
RISK_ADJUSTMENT_MULTIPLIER = 0.15

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "to", "of", "in", "on", "for",
    "with", "as", "at", "by", "from", "is", "are", "was", "were", "be", "been", "being",
    "that", "this", "these", "those", "it", "its", "their", "his", "her", "they", "them",
}
NEGATION_CONTEXTS = [
    "debunk", "refut", "false claim", "disprove", "not true", "incorrect",
    "misleading claim", "fact check", "verify", "investigated", "found no evidence", "contrary to",
]
SUSPICIOUS_TEXT_PATTERNS = [
    "fake news", "hoax", "conspiracy", "exposed", "scandal", "unverified", "rumor",
    "without evidence", "anonymous source", "anonymous sources", "deep state", "cover-up",
    "suppressed report", "viral claim", "social media posts claim", "no official confirmation",
    "not yet been published", "leaked", "secret agenda", "do your own research",
    "hidden cure", "global elites", "secretly confirmed", "insiders revealed", "undeniable proof",
    "suppressed the report", "interdimensional beings", "covert operation", "global internet shutdown",
    "reportedly approved", "no official press release", "insiders have confirmed",
    "closed-door emergency meeting", "not yet been peer-reviewed", "technical reports are still pending",
    "unlimited energy", "without any environmental impact",
]
FACTUAL_CUES = [
    "according to", "official report", "peer-reviewed", "peer reviewed", "data shows", "study found",
    "confirmed by", "documented", "audit", "evidence", "court ruled", "committee said",
    "ministry said", "agency said", "official statement", "statistics agency", "regulatory filing",
    "meeting minutes",
]
UNCERTAINTY_CUES = [
    "without evidence", "rumor", "allegedly", "unverified", "anonymous source",
    "social media posts claim", "not yet been published", "no official confirmation",
    "reportedly approved", "no official press release", "insiders have confirmed",
    "closed-door emergency meeting", "source we cannot name", "cannot be independently verified",
    "people in the know", "not yet been peer-reviewed", "technical reports are still pending",
    "reports are still pending",
]
EVIDENCE_MARKERS = [
    "according to", "official report", "official statement", "ministry said", "agency said", "court filing",
    "court ruled", "committee said", "regulator said", "documented", "audit", "data shows", "study found",
    "survey found", "peer-reviewed", "published in", "regulatory filing", "meeting minutes", "senator said",
    "president said", "spokesman said", "spokeswoman said", "posted on", "tweeted", "told reporters",
    "in a statement", "press conference", "news conference", "briefing",
]
ATTRIBUTION_MARKERS = [
    "according to", "officials said", "authorities said", "spokesperson said", "minister said", "agency said",
    "ministry said", "court filing", "court said", "committee said", "regulator said", "police said",
    "researchers said", "the report said", "the study said", "announced in a statement", "issued a statement",
    "published a report", "senator said", "congressman said", "lawmaker said", "diplomat said",
    "foreign minister", "prime minister", "president said", "white house said", "pentagon said",
    "state department", "told reporters", "in an interview",
]
GROUNDING_MARKERS = [
    "court", "ministry", "agency", "committee", "central bank", "parliament", "government", "police",
    "journal", "study", "survey", "audit", "statistics", "report", "filing", "statement", "investigation",
    "research team", "researchers", "review board", "regulator", "senator", "congressman", "lawmaker",
    "diplomat", "official", "president", "prime minister", "foreign minister", "state department",
    "pentagon", "white house", "european", "nato", "united nations",
]
CLAIM_UNCERTAINTY_MARKERS = [
    "unverified", "rumor", "allegedly", "sources say", "it is believed", "not yet been published",
    "no official confirmation", "social media posts claim", "secretly", "hidden cure", "global elites",
    "insiders revealed", "undeniable proof", "interdimensional beings", "covert operation",
    "reportedly approved", "no official press release", "insiders have confirmed",
    "closed-door emergency meeting", "not yet been peer-reviewed", "technical reports are still pending",
    "claim to have discovered", "being hailed as", "insider", "whistleblower", "classified document",
    "leaked document", "surfaces online", "share before deletion", "quietly signed",
    "finally revealed", "mainstream refuses to report", "they are hiding this",
]
SENSATIONAL_MARKERS = [
    "shocking", "unbelievable", "explosive", "bombshell", "secret", "you won't believe",
    "jaw-dropping", "breaking!!!", "secretly confirmed", "interdimensional", "miracle", "stunned", "baffled",
]
PROMOTIONAL_MARKERS = [
    "defining moment", "world leader", "futuristic", "bold and forward-thinking", "transforming",
    "millions of jobs", "revolutionary", "historic initiative", "promises to create", "positioning as",
    "breakthrough is being hailed", "revolutionary step", "solving global energy challenges",
]
TEMPLATED_NARRATIVE_MARKERS = [
    "in a surprising turn of events", "has sparked widespread debate", "supporters have praised",
    "critics have raised concerns", "a defining moment for", "aimed at transforming", "dubbed",
]
EXTRAORDINARY_CLAIM_MARKERS = [
    "unlimited energy", "without any environmental impact", "solving global energy challenges",
    "miracle cure", "changes everything",
]
CONSPIRATORIAL_MARKERS = [
    "deep state", "cover-up", "cover up", "global bankers", "globalist cabal", "cabal", "crisis actors",
    "chemtrails", "plandemic", "population control", "mind control", "false flag", "secret tribunal",
    "bank account freeze", "all cancers", "all disease", "overnight", "shadow government",
]

_SOURCES: Dict[str, float] | None = None
_NEGATIVE_TERMS: Dict[str, float] | None = None
_SUSPICIOUS_PHRASES: List[str] | None = None
_BRIDGE_READY = False


@dataclass
class AlgorithmAssessment:
    overall_score: float
    verdict: str
    module_scores: Dict[str, float]
    explanations: List[str]
    suspicious_phrases: List[str] = field(default_factory=list)
    top_negative_terms: List[Dict] = field(default_factory=list)
    greedy_signals: List[Dict] = field(default_factory=list)
    claim_flags: List[str] = field(default_factory=list)
    source_label: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def clamp_score(score: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, score))


def to_lower_copy(text: str) -> str:
    return (text or "").lower()


def count_phrase_hits(text: str, phrases: List[str]) -> int:
    return sum(text.count(phrase) for phrase in phrases)


def count_positive_phrase_hits(text: str, phrases: List[str]) -> int:
    return sum(1 for phrase in phrases if phrase in text)


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9']+", to_lower_copy(text))


def remove_stop_words(tokens: List[str]) -> List[str]:
    return [token for token in tokens if token not in STOP_WORDS]


def split_tokens(text: str) -> List[str]:
    return [token for token in text.split() if token]


def normalize_source_name(source_name: str) -> str:
    normalized = []
    previous_space = False
    for char in source_name or "":
        if char.isalnum():
            normalized.append(char.lower())
            previous_space = False
        elif char.isspace() or char in "./-_|":
            if normalized and not previous_space:
                normalized.append(" ")
                previous_space = True
    normalized_text = "".join(normalized).strip()
    tokens = split_tokens(normalized_text)
    if tokens and tokens[0] == "www":
        tokens = tokens[1:]
    while len(tokens) > 1 and tokens[-1] in {"com", "org", "net", "co", "io", "uk", "us", "in", "ca", "au"}:
        tokens.pop()
    if len(tokens) > 1 and tokens[0] == "the":
        tokens = tokens[1:]
    return " ".join(tokens)


def _load_sources() -> Dict[str, float]:
    global _SOURCES
    if _SOURCES is not None:
        return _SOURCES

    _SOURCES = {}
    if SOURCE_FILE.exists():
        with SOURCE_FILE.open() as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                source_name = normalize_source_name(row.get("source", ""))
                numeric_value = None
                for key in ("credibility", "status"):
                    try:
                        numeric_value = float((row.get(key) or "").strip())
                        break
                    except ValueError:
                        continue
                if source_name and numeric_value is not None:
                    _SOURCES[source_name] = numeric_value
    return _SOURCES


def _load_negative_terms() -> Dict[str, float]:
    global _NEGATIVE_TERMS
    if _NEGATIVE_TERMS is not None:
        return _NEGATIVE_TERMS

    _NEGATIVE_TERMS = {}
    if NEGATIVE_TERMS_FILE.exists():
        with NEGATIVE_TERMS_FILE.open() as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                _NEGATIVE_TERMS[row["term"].strip().lower()] = float(row["weight"])
    return _NEGATIVE_TERMS


def _load_suspicious_phrases() -> List[str]:
    global _SUSPICIOUS_PHRASES
    if _SUSPICIOUS_PHRASES is not None:
        return _SUSPICIOUS_PHRASES

    if SUSPICIOUS_PHRASES_FILE.exists():
        _SUSPICIOUS_PHRASES = [line.strip().lower() for line in SUSPICIOUS_PHRASES_FILE.read_text().splitlines() if line.strip()]
    else:
        _SUSPICIOUS_PHRASES = []
    return _SUSPICIOUS_PHRASES


def validate_source(source_name: str) -> tuple[float, str]:
    sources = _load_sources()
    normalized = normalize_source_name(source_name or "")
    if normalized in sources:
        score = sources[normalized]
    else:
        input_tokens = split_tokens(normalized)
        best_score = -1.0
        best_overlap = 0
        for candidate, candidate_score in sources.items():
            candidate_tokens = set(split_tokens(candidate))
            if input_tokens and all(token in candidate_tokens for token in input_tokens):
                if len(input_tokens) > best_overlap or (len(input_tokens) == best_overlap and candidate_score > best_score):
                    best_overlap = len(input_tokens)
                    best_score = candidate_score
        score = best_score if best_score >= 0 else 50.0

    if score >= 70:
        label = "trusted"
    elif score <= 35:
        label = "untrusted"
    else:
        label = "neutral"
    return score, label


def find_suspicious_phrases(text: str) -> List[str]:
    normalized = to_lower_copy(text)
    return [phrase for phrase in _load_suspicious_phrases() if phrase in normalized]


def is_negation_context(text: str, pos: int) -> bool:
    start = max(0, pos - 50)
    context = text[start:pos]
    return any(neg in context for neg in NEGATION_CONTEXTS)


def count_context_aware_hits(text: str, patterns: List[str]) -> int:
    hits = 0
    for pattern in patterns:
        pos = text.find(pattern)
        while pos != -1:
            if not is_negation_context(text, pos):
                hits += 1
            pos = text.find(pattern, pos + 1)
    return hits


def rabin_karp_unique_hits(text: str, patterns: List[str]) -> int:
    return sum(1 for pattern in patterns if pattern in text)


def analyze_frequency(tokens: List[str], normalized_text: str) -> tuple[float, List[Dict]]:
    negative_terms = _load_negative_terms()
    frequency_map = Counter(tokens)

    for term in negative_terms:
        if " " in term:
            occurrences = len(re.findall(rf"(?<!\w){re.escape(term)}(?!\w)", normalized_text))
            if occurrences:
                frequency_map[term] += occurrences

    scored_terms = []
    total_suspicion = 0.0
    for term, frequency in frequency_map.items():
        weight = negative_terms.get(term)
        if weight is None or frequency <= 0:
            continue
        suspicion = weight * (1.0 - math.exp(-0.3 * frequency)) * 100.0
        total_suspicion += suspicion
        scored_terms.append({
            "term": term,
            "frequency": frequency,
            "suspicion_level": round(suspicion, 2),
        })

    scored_terms.sort(key=lambda item: item["suspicion_level"], reverse=True)
    return min(100.0, total_suspicion), scored_terms[:3]


def _load_temporal_history() -> List[Dict]:
    if not TEMPORAL_HISTORY_FILE.exists():
        return []
    try:
        return json.loads(TEMPORAL_HISTORY_FILE.read_text())
    except Exception:
        return []


def _save_temporal_history(entries: List[Dict]) -> None:
    TEMPORAL_HISTORY_FILE.write_text(json.dumps(entries[-200:]))


def analyze_temporal(source: str, token_count: int, timestamp: datetime) -> float:
    normalized_source = normalize_source_name(source or "unknown")
    now = timestamp.astimezone(timezone.utc)
    cutoff = now - timedelta(hours=TEMPORAL_WINDOW_HOURS)
    history = _load_temporal_history()
    history = [entry for entry in history if datetime.fromisoformat(entry["timestamp"]) >= cutoff]
    source_entries = [entry["frequency"] for entry in history if entry["term"] == normalized_source]
    source_entries.append(token_count)
    history.append({"term": normalized_source, "frequency": token_count, "timestamp": now.isoformat()})
    _save_temporal_history(history)

    if len(source_entries) < 2:
        return 0.0

    mean = sum(source_entries) / len(source_entries)
    variance = sum((value - mean) ** 2 for value in source_entries) / len(source_entries)
    stddev = math.sqrt(variance)
    if stddev <= 0:
        return 0.0
    z_score = (source_entries[-1] - mean) / stddev
    return min(100.0, max(0.0, (z_score / 5.0) * 100.0))


def detect_greedy_signals(headline: str, body: str) -> tuple[float, List[Dict]]:
    sensational_words = [
        "unprecedented", "unbelievable", "shocking", "astonishing", "incredible", "amazing",
        "stunning", "astounding", "bombshell", "explosive", "sensational", "jaw-dropping", "mind-blowing",
    ]
    clickbait_patterns = [
        "you won't believe", "this one trick", "doctors hate", "click here", "see what",
        "find out", "what happens next", "you won't", "shocking truth",
    ]
    urgency_words = ["immediate", "urgent", "limited time", "hurry", "don't wait", "act now", "last chance"]
    emotional_words = [
        "disgusting", "outrageous", "horrified", "enraged", "heartbroken", "devastated",
        "shocked", "appalled", "furious", "sickening",
    ]

    def lower(text: str) -> str:
        return to_lower_copy(text)

    def detect_all_caps(text: str) -> bool:
        letters = [char for char in text if char.isalpha()]
        if not letters:
            return False
        return sum(1 for char in letters if char.isupper()) / len(letters) > 0.5

    def count_char(text: str, char: str) -> int:
        return text.count(char)

    signals = []
    lower_headline = lower(headline)
    lower_body = lower(body)

    def push(triggered: bool, name: str, severity: float) -> None:
        if triggered:
            signals.append({"pattern_name": name, "severity": severity})

    push(detect_all_caps(headline), "ALL_CAPS", 1.0)
    push(count_char(lower_headline, "!") > 2, "EXCESSIVE_EXCLAMATION", 1.0)
    push(count_char(lower_headline, "?") > 2, "EXCESSIVE_QUESTION", 0.9)
    push(any(word in lower_headline for word in sensational_words), "SENSATIONAL_WORDS", 1.0)
    push(any(pattern in lower_headline for pattern in clickbait_patterns), "CLICKBAIT_STRUCTURE", 1.0)
    push(sum(word in lower_headline for word in urgency_words) >= 2, "URGENCY_TACTICS", 1.0)
    push(sum(word in lower_headline for word in emotional_words) >= 2, "EMOTIONAL_MANIPULATION", 1.0)

    push(detect_all_caps(body), "BODY_ALL_CAPS", 0.8)
    push(count_char(lower_body, "!") > 2, "BODY_EXCESSIVE_EXCLAMATION", 0.7)
    push(any(pattern in lower_body for pattern in clickbait_patterns), "BODY_CLICKBAIT_STRUCTURE", 0.85)

    top_signals = sorted(signals, key=lambda item: item["severity"], reverse=True)[:3]
    total_score = 0.0
    weight = 1.0
    for signal in top_signals:
        total_score += signal["severity"] * weight * 100.0
        weight *= 0.5
    return min(100.0, total_score), top_signals


def assess_claim_verifiability(headline: str, body: str) -> tuple[float, List[str]]:
    text = to_lower_copy(f"{headline} {body}")
    evidence_hits = count_positive_phrase_hits(text, EVIDENCE_MARKERS)
    attribution_hits = count_positive_phrase_hits(text, ATTRIBUTION_MARKERS)
    uncertainty_hits = count_phrase_hits(text, CLAIM_UNCERTAINTY_MARKERS)
    sensational_hits = count_phrase_hits(text, SENSATIONAL_MARKERS)
    promotional_hits = count_phrase_hits(text, PROMOTIONAL_MARKERS)
    grounding_hits = count_phrase_hits(text, GROUNDING_MARKERS)
    template_hits = count_phrase_hits(text, TEMPLATED_NARRATIVE_MARKERS)
    extraordinary_hits = count_phrase_hits(text, EXTRAORDINARY_CLAIM_MARKERS)
    conspiratorial_hits = count_phrase_hits(text, CONSPIRATORIAL_MARKERS)
    numeric_claims = len(re.findall(r"\b\d+\b", text))
    has_quotes = '"' in headline or '"' in body or bool(re.search(r"(?<![A-Za-z])'(?![A-Za-z])", headline + " " + body))
    weak_support = evidence_hits == 0 and attribution_hits == 0 and grounding_hits < 2
    has_grounded_specificity = grounding_hits >= 2 and (evidence_hits > 0 or attribution_hits > 0 or numeric_claims > 0)

    score = 50.0
    score += min(25.0, evidence_hits * 6.0)
    score += min(15.0, attribution_hits * 4.0)
    score += min(12.0, grounding_hits * 2.5)
    if not weak_support:
        score += min(6.0, numeric_claims * 1.5)
    if has_quotes:
        score += 4.0
    if has_grounded_specificity:
        score += 5.0

    score -= min(28.0, uncertainty_hits * 5.5)
    score -= min(20.0, sensational_hits * 5.0)
    score -= min(24.0, promotional_hits * 6.0)
    score -= min(28.0, conspiratorial_hits * 5.5)

    flags: List[str] = []
    if numeric_claims > 0 and weak_support:
        score -= 8.0
        flags.append("Numeric claims without evidence or attribution")
    if re.search(r"\b20[2-9]\d\b", text) and evidence_hits == 0:
        score -= 6.0
        flags.append("Future-year claim without explicit evidence")
    if template_hits >= 4 and evidence_hits == 0:
        score -= 14.0
        flags.append("Templated narrative style with weak sourcing")
    if len(text.split()) > 100 and weak_support:
        score -= 8.0
        flags.append("Long narrative with no concrete sourcing markers")
    if "no official press release" in text or "no official statement" in text:
        score -= 10.0
        flags.append("Claim references lack of official press release")
    if "insiders have confirmed" in text and evidence_hits == 0:
        score -= 8.0
        flags.append("Insider-only sourcing without verifiable evidence")
    if "closed-door emergency meeting" in text and evidence_hits == 0:
        score -= 6.0
        flags.append("Closed-door emergency claim without primary evidence")
    if conspiratorial_hits > 0:
        flags.append("Conspiratorial framing reduces verifiability")
    if promotional_hits > 0 and evidence_hits == 0:
        flags.append("Promotional framing with weak verifiability")
    if weak_support and uncertainty_hits > 0:
        score -= 8.0
        flags.append("Uncertain claim lacks concrete sourcing")
    if evidence_hits == 0 and promotional_hits > 0 and uncertainty_hits > 0:
        score -= 6.0
        flags.append("Promotional uncertain framing")
    if extraordinary_hits > 0 and (evidence_hits == 0 or uncertainty_hits > 0):
        score -= min(18.0, extraordinary_hits * 9.0)
        flags.append("Extraordinary claim lacks strong verification")
    return clamp_score(score), flags


def assess_algorithmic_credibility(headline: str, body: str, source: str, timestamp_iso: str | None = None) -> AlgorithmAssessment:
    bridge_result = _run_cxx_bridge(headline, body, source)

    combined_text = f"{headline} {body}".strip()
    normalized_text = to_lower_copy(combined_text)
    tokens = remove_stop_words(tokenize(combined_text))
    factual_hits = count_positive_phrase_hits(normalized_text, FACTUAL_CUES)
    uncertainty_hits = count_phrase_hits(normalized_text, UNCERTAINTY_CUES)
    short_text_penalty = SHORT_TEXT_PENALTY_CRITICAL if len(tokens) < SHORT_TEXT_THRESHOLD_CRITICAL else SHORT_TEXT_PENALTY_WARNING if len(tokens) < SHORT_TEXT_THRESHOLD_WARNING else 0.0
    preprocessing_score = clamp_score(BASELINE_PREPROCESSING_SCORE + factual_hits * FACTUAL_CUE_BONUS - uncertainty_hits * UNCERTAINTY_PENALTY - short_text_penalty)

    source_score, source_label = validate_source(source)
    suspicious_phrases = find_suspicious_phrases(combined_text)
    phrase_score = clamp_score(BASE_SCORE - min(MAX_PHRASE_PENALTY, len(suspicious_phrases) * PHRASE_PENALTY_PER_HIT))
    kmp_matches = count_context_aware_hits(normalized_text, SUSPICIOUS_TEXT_PATTERNS)
    kmp_score = clamp_score(BASE_SCORE - min(MAX_KMP_PENALTY, kmp_matches * KMP_PENALTY_PER_HIT))
    rk_hits = rabin_karp_unique_hits(normalized_text, SUSPICIOUS_TEXT_PATTERNS)
    rabin_karp_score = clamp_score(BASE_SCORE - min(MAX_RABIN_KARP_PENALTY, rk_hits * RABIN_KARP_PENALTY_PER_HIT))
    frequency_suspicion, top_negative_terms = analyze_frequency(tokens, normalized_text)
    frequency_score = clamp_score(BASE_SCORE - min(MAX_FREQUENCY_PENALTY, frequency_suspicion * FREQUENCY_PENALTY_MULTIPLIER))

    timestamp = datetime.now(timezone.utc)
    if timestamp_iso:
        try:
            timestamp = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            pass
    temporal_spike = analyze_temporal(source or "unknown", len(tokens), timestamp)
    temporal_score = clamp_score(BASE_SCORE - temporal_spike)
    greedy_manipulation, greedy_signals = detect_greedy_signals(headline, body)
    greedy_score = clamp_score(BASE_SCORE - greedy_manipulation)
    claim_score, claim_flags = assess_claim_verifiability(headline, body)

    low_risk_structure = not suspicious_phrases and kmp_matches == 0 and rk_hits == 0 and greedy_manipulation < 15.0 and uncertainty_hits <= 1 and frequency_suspicion < SUSPICION_THRESHOLD
    high_quality_article = source_score >= HIGH_SOURCE_THRESHOLD and claim_score >= 60.0 and factual_hits >= 1

    risk_penalty = 0.0
    if source_score <= VERY_LOW_SOURCE_THRESHOLD:
        risk_penalty += RISK_PENALTY_VERY_LOW_SOURCE
    elif source_score < LOW_SOURCE_CREDIBILITY_THRESHOLD:
        risk_penalty += RISK_PENALTY_LOW_SOURCE
    if source_score <= MEDIUM_SOURCE_CREDIBILITY_THRESHOLD and claim_score < 58.0 and not low_risk_structure:
        risk_penalty += RISK_PENALTY_LOW_CLAIM_AND_SOURCE
    if kmp_matches >= 2 or greedy_manipulation > MANIPULATION_THRESHOLD or frequency_suspicion > SUSPICION_THRESHOLD:
        risk_penalty += RISK_PENALTY_SUSPICIOUS_PATTERNS * (0.6 if source_score >= HIGH_SOURCE_THRESHOLD else 1.0)
    if uncertainty_hits > 1 and factual_hits == 0 and not high_quality_article:
        risk_penalty += min(RISK_PENALTY_MAX_UNCERTAINTY, (uncertainty_hits - 1) * RISK_PENALTY_PER_UNCERTAINTY)
    if claim_score < LOW_CLAIM_VERIFIABILITY_THRESHOLD and not high_quality_article:
        risk_penalty += (LOW_CLAIM_VERIFIABILITY_THRESHOLD - claim_score) * (0.15 if low_risk_structure else RISK_PENALTY_CLAIM_MULTIPLIER)
    if source_score < LOW_SOURCE_CREDIBILITY_THRESHOLD and claim_score < LOW_CLAIM_VERIFIABILITY_THRESHOLD:
        risk_penalty += RISK_PENALTY_COMBINED_LOW

    consistency_boost = 0.0
    if high_quality_article and low_risk_structure:
        consistency_boost += CONSISTENCY_BOOST_FACTUAL
    if claim_score >= 70.0:
        consistency_boost += CONSISTENCY_BOOST_HIGH_CLAIM
    if source_score >= 50.0 and claim_score >= 45.0 and low_risk_structure:
        consistency_boost += CONSISTENCY_BOOST_CLEAN_RECORD
    if source_score >= HIGH_SOURCE_THRESHOLD:
        consistency_boost += CONSISTENCY_BOOST_TRUSTED_SOURCE
    consistency_boost = min(consistency_boost, MAX_CONSISTENCY_BOOST)

    detection_average = (phrase_score + kmp_score + rabin_karp_score + frequency_score + temporal_score + greedy_score) / 6.0
    credibility_core = (source_score * SOURCE_WEIGHT) + (claim_score * CLAIM_WEIGHT) + (preprocessing_score * PREPROCESSING_WEIGHT) + (detection_average * DETECTION_WEIGHT)
    risk_adjustment = (detection_average - RISK_ADJUSTMENT_CENTER) * RISK_ADJUSTMENT_MULTIPLIER
    overall_score = clamp_score(credibility_core + risk_adjustment - risk_penalty + consistency_boost, 0.0, 97.0)
    module_scores = {
        "preprocessing": round(preprocessing_score, 2),
        "source_validation": round(source_score, 2),
        "phrase_indexing": round(phrase_score, 2),
        "kmp_matching": round(kmp_score, 2),
        "rabin_karp": round(rabin_karp_score, 2),
        "frequency_analysis": round(frequency_score, 2),
        "temporal_analysis": round(temporal_score, 2),
        "greedy_filtering": round(greedy_score, 2),
        "claim_verifiability": round(claim_score, 2),
    }

    if overall_score >= 80:
        verdict = "likely_original"
    elif overall_score >= 55:
        verdict = "unverified"
    else:
        verdict = "likely_fake_false"

    explanations = [
        f"[Preprocessing] Score: {preprocessing_score:.1f}/100 - Tokens: {len(tokens)}, factual cues: {factual_hits}, uncertainty cues: {uncertainty_hits}",
        f"[Source Validation] Score: {source_score:.1f}/100 - Source: {source or 'Unknown'} ({source_label})",
        f"[Phrase Indexing] Score: {phrase_score:.1f}/100 - Found {len(suspicious_phrases)} suspicious phrase(s)",
        f"[KMP Matching] Score: {kmp_score:.1f}/100 - KMP found {kmp_matches} suspicious pattern(s)",
        f"[Rabin-Karp] Score: {rabin_karp_score:.1f}/100 - Rabin-Karp found {rk_hits} unique suspicious pattern(s)",
        f"[Frequency Analysis] Score: {frequency_score:.1f}/100 - Found {len(top_negative_terms)} negative term(s)",
        f"[Temporal Analysis] Score: {temporal_score:.1f}/100 - Temporal spike score: {temporal_spike:.1f}/100",
        f"[Greedy Filtering] Score: {greedy_score:.1f}/100 - Detected {len(greedy_signals)} manipulation signal(s)",
        f"[Claim Verifiability] Score: {claim_score:.1f}/100 - Claim flags: {len(claim_flags)}",
    ]
    if risk_penalty > 0.0 or consistency_boost > 0.0:
        explanations.append(f"[Score Calibration] Risk calibration applied (penalty: {risk_penalty:.1f}, boost: {consistency_boost:.1f})")

    return AlgorithmAssessment(
        overall_score=round(bridge_result["overall_score"], 2) if bridge_result else round(overall_score, 2),
        verdict=bridge_result["verdict"] if bridge_result else verdict,
        module_scores=bridge_result["module_scores"] if bridge_result else module_scores,
        explanations=bridge_result["explanations"] if bridge_result else explanations,
        suspicious_phrases=suspicious_phrases[:5],
        top_negative_terms=top_negative_terms,
        greedy_signals=greedy_signals,
        claim_flags=claim_flags[:5],
        source_label=source_label,
    )


def _ensure_bridge_binary() -> bool:
    global _BRIDGE_READY
    if _BRIDGE_READY and BRIDGE_BINARY.exists():
        return True
    if not BRIDGE_BUILD_SCRIPT.exists():
        return False
    try:
        subprocess.run(["chmod", "+x", str(BRIDGE_BUILD_SCRIPT)], check=True, cwd=str(PROJECT_ROOT))
        subprocess.run([str(BRIDGE_BUILD_SCRIPT)], check=True, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    except Exception:
        return False
    _BRIDGE_READY = BRIDGE_BINARY.exists()
    return _BRIDGE_READY


def _run_cxx_bridge(headline: str, body: str, source: str) -> Dict | None:
    if not _ensure_bridge_binary():
        return None
    try:
        completed = subprocess.run(
            [
                str(BRIDGE_BINARY),
                "--headline", headline,
                "--body", body,
                "--source", source or "Unknown Source",
                "--sources-csv", str(SOURCE_FILE),
                "--phrases-file", str(SUSPICIOUS_PHRASES_FILE),
                "--negative-terms-file", str(NEGATIVE_TERMS_FILE),
            ],
            check=True,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)
    except Exception:
        return None
