"""
Direct text analysis entry point for Factify.

Usage:
  python analyze_text.py --text "Some news claim" --format json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ml.algorithms.credibility_engine import assess_algorithmic_credibility
from src.ml.algorithms.universal_facts import detect_universal_fact_contradictions, detect_verified_universal_facts
from src.ml.models.fake_news_predictor import DetectionResult, classify_with_algorithm_score
from src.ml.models.tweet_fake_predictor import analyze_tweet_text

_DATE_RE = re.compile(
    r"""
    (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|
       Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|
       Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}
    |
    \d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}
    |
    \d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}
    """,
    re.VERBOSE | re.IGNORECASE,
)
_SENSATIONAL_RE = re.compile(
    r"\b(BREAKING|SHOCKING|BOMBSHELL|EXPLOSIVE|OUTRAGE|SECRET|EXPOSED|"
    r"SCANDAL|HOAX|CONSPIRACY|URGENT|MUST.?READ|YOU WON.?T BELIEVE|"
    r"CLICK HERE|SHARE NOW|GOING VIRAL)\b",
    re.IGNORECASE,
)
_CAPS_RE = re.compile(r"\b[A-Z]{4,}\b")
@dataclass
class TextAnalysisResult:
    combined_text: str = ""
    headline: str = "None"
    body: str = "None"
    dates: List[str] = field(default_factory=list)
    people: List[str] = field(default_factory=list)
    organizations: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    source: str = "None"
    suspicious_elements: List[str] = field(default_factory=list)
    image_path: str = ""
    image_type: str = "text"
    engine_used: str = "direct-text"
    ocr_region_count: int = 0
    caption: str = ""
    processing_time_sec: float = 0.0
    raw_ocr_text: str = ""
    input_type: str = "text"
    url: str = ""
    detection: dict = field(default_factory=dict)
    algorithms: dict = field(default_factory=dict)
    tweet_model: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _extract_headline(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "None"
    first_line = lines[0]
    return first_line[:160] if first_line else "None"


def _detect_suspicious(text: str) -> List[str]:
    flags = []
    caps = sorted(set(_CAPS_RE.findall(text)))
    if len(caps) > 3:
        flags.append(f"Excessive ALL-CAPS ({', '.join(caps[:5])})")
    hits = sorted(set(_SENSATIONAL_RE.findall(text)))
    if hits:
        flags.append(f"Sensational language ({', '.join(hits)})")
    if len(text.split()) < 25:
        flags.append("Very short claim or article snippet")
    if detect_universal_fact_contradictions(text):
        flags.append("Known factual contradiction detected in the claim")
    return flags


def build_result(text: str) -> TextAnalysisResult:
    started_at = time.time()
    cleaned = re.sub(r"\s+", " ", text).strip()
    headline = _extract_headline(text)
    suspicious = _detect_suspicious(cleaned)
    algorithms = assess_algorithmic_credibility(headline, cleaned, "User provided text").to_dict()
    base_detection = classify_with_algorithm_score(cleaned, algorithms["overall_score"], suspicious, "User provided text")
    tweet_model = analyze_tweet_text(cleaned)
    detection = _blend_text_detection(base_detection, tweet_model.to_dict())
    detection = _apply_text_guardrails(cleaned, detection, algorithms, tweet_model.to_dict()).to_dict()

    return TextAnalysisResult(
        combined_text=cleaned,
        headline=headline,
        body=cleaned,
        dates=list(dict.fromkeys(_DATE_RE.findall(cleaned))),
        suspicious_elements=suspicious,
        processing_time_sec=round(time.time() - started_at, 2),
        raw_ocr_text=cleaned,
        detection=detection,
        algorithms=algorithms,
        tweet_model=tweet_model.to_dict(),
    )


def _blend_text_detection(base_detection: DetectionResult, tweet_model: dict) -> DetectionResult:
    if not tweet_model.get("enabled"):
        return base_detection

    coverage_ratio = float(tweet_model.get("coverage_ratio") or 0.0)
    tweet_confidence = float(tweet_model.get("confidence_score") or 0.0)
    
    # If coverage is very low (<15%), dramatically reduce tweet model influence
    if coverage_ratio < 15.0:
        return base_detection
    
    coverage_factor = min(1.0, coverage_ratio / 100.0)
    confidence_factor = min(1.0, tweet_confidence / 100.0)
    tweet_weight = min(0.18, 0.05 + (coverage_factor * confidence_factor * 0.9))
    if tweet_confidence < 20:
        tweet_weight = min(tweet_weight, 0.08)
    if tweet_model.get("verdict") == "unverified":
        tweet_weight *= 0.8

    tweet_fake_probability = int(tweet_model.get("fake_probability") or 0)
    blended_fake_probability = int(round((base_detection.fake_probability * (1.0 - tweet_weight)) + (tweet_fake_probability * tweet_weight)))
    blended_original_probability = 100 - blended_fake_probability
    blended_confidence = int(round((base_detection.confidence_score * (1.0 - tweet_weight)) + ((tweet_model.get("confidence_score") or 0) * tweet_weight)))

    if blended_confidence >= 70:
        confidence = "high"
    elif blended_confidence >= 40:
        confidence = "medium"
    else:
        confidence = "low"

    if blended_fake_probability >= 67:
        verdict = "likely_fake_false"
        verdict_label = "Likely Fake / False"
        summary = "The text verdict is elevated by both the core article model and the tweet-style classifier."
    elif blended_fake_probability <= 33:
        verdict = "likely_original"
        verdict_label = "Likely Original"
        summary = "The text verdict remains in the lower-risk band across the article model and tweet-style classifier."
    else:
        verdict = "unverified"
        verdict_label = "Unverified"
        summary = "The text remains mixed after combining the article model, deterministic checks, and tweet-style classifier."

    findings = list(base_detection.findings)
    findings.append(
        f"Tweet-style text model: {tweet_fake_probability}% fake risk from {tweet_model.get('derived_feature_count', 0)}/{tweet_model.get('feature_count', 0)} derived features."
    )
    contradiction_hit = any("factual contradiction" in finding.lower() for finding in findings)
    if contradiction_hit:
        blended_fake_probability = max(blended_fake_probability, 82)
        blended_original_probability = 100 - blended_fake_probability
        blended_confidence = max(blended_confidence, 72)
        confidence = "high"
        verdict = "likely_fake_false"
        verdict_label = "Likely Fake / False"
        summary = "The claim matches a known factual contradiction, so the result is pushed into the high-risk band."

    return DetectionResult(
        verdict=verdict,
        verdict_label=verdict_label,
        raw_score=base_detection.raw_score,
        fake_probability=blended_fake_probability,
        original_probability=blended_original_probability,
        confidence=confidence,
        confidence_score=min(blended_confidence, 100),
        summary=summary,
        findings=list(dict.fromkeys(findings))[:5],
    )


def _apply_text_guardrails(text: str, detection: DetectionResult, algorithms: dict, tweet_model: dict) -> DetectionResult:
    algorithm_score = float(algorithms.get("overall_score") or 0.0)
    algorithm_verdict = algorithms.get("verdict")
    tweet_confidence = float(tweet_model.get("confidence_score") or 0.0)
    contradiction_flag = any("factual contradiction" in flag.lower() for flag in algorithms.get("claim_flags", []))
    verified_fact_hits = detect_verified_universal_facts(text)

    if contradiction_flag:
        return detection

    if verified_fact_hits:
        findings = list(dict.fromkeys(detection.findings + ["Claim matches a verified universal fact pattern."]))
        return DetectionResult(
            verdict="likely_original",
            verdict_label="Likely Original",
            raw_score=detection.raw_score,
            fake_probability=min(detection.fake_probability, 24),
            original_probability=max(detection.original_probability, 76),
            confidence="high",
            confidence_score=max(detection.confidence_score, 72),
            summary="The claim matches a verified universal fact pattern, so the result is promoted into the low-risk band.",
            findings=findings[:5],
        )

    if algorithm_verdict == "likely_original" and algorithm_score >= 92.0 and tweet_confidence <= 20.0:
        findings = list(dict.fromkeys(detection.findings + ["Deterministic credibility checks strongly support a grounded report."]))
        return DetectionResult(
            verdict="likely_original",
            verdict_label="Likely Original",
            raw_score=detection.raw_score,
            fake_probability=min(detection.fake_probability, 28),
            original_probability=max(detection.original_probability, 72),
            confidence="high" if detection.confidence_score >= 60 else "medium",
            confidence_score=max(detection.confidence_score, 68),
            summary="Strong deterministic credibility signals outweigh the low-confidence tweet-text model for this report.",
            findings=findings[:5],
        )

    return detection


def main():
    parser = argparse.ArgumentParser(description="Analyze raw text for fake news signals")
    parser.add_argument("--text", required=True, help="Text to analyze (max 100,000 characters)")
    parser.add_argument("--format", dest="fmt", choices=["txt", "json"], default="json")
    args = parser.parse_args()

    # Validate text length to prevent memory exhaustion
    if len(args.text) > 100000:
        error_result = {
            "error": "Text too large (max 100,000 characters)",
            "text_length": len(args.text)
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)

    if len(args.text.strip()) < 5:
        error_result = {
            "error": "Text too short (minimum 5 characters)",
            "text_length": len(args.text)
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)

    try:
        result = build_result(args.text)
        if args.fmt == "txt":
            print(result.body)
        else:
            print(json.dumps(result.to_dict(), indent=2))
    except Exception as e:
        error_result = {
            "error": f"Analysis failed: {str(e)}",
            "type": type(e).__name__
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
