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
from src.ml.models.fake_news_predictor import classify_text, classify_with_algorithm_assessment

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
    return flags


def build_result(text: str) -> TextAnalysisResult:
    return build_result_with_options(text, use_algorithms=True)


def build_result_with_options(text: str, use_algorithms: bool = True) -> TextAnalysisResult:
    started_at = time.time()
    cleaned = re.sub(r"\s+", " ", text).strip()
    headline = _extract_headline(text)
    suspicious = _detect_suspicious(cleaned)
    if use_algorithms:
        algorithms = assess_algorithmic_credibility(headline, cleaned, "User provided text").to_dict()
        detection = classify_with_algorithm_assessment(cleaned, algorithms, suspicious, "User provided text").to_dict()
    else:
        algorithms = {
            "enabled": False,
            "overall_score": 0,
            "verdict": "unverified",
            "module_scores": {},
            "explanations": ["Algorithm scoring was disabled for this run."],
            "suspicious_phrases": [],
            "top_negative_terms": [],
            "greedy_signals": [],
            "claim_flags": [],
            "ai_flags": [],
            "source_label": "disabled",
        }
        detection = classify_text(cleaned, suspicious, "User provided text").to_dict()

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
    )


def main():
    parser = argparse.ArgumentParser(description="Analyze raw text for fake news signals")
    parser.add_argument("--text", required=True, help="Text to analyze (max 100,000 characters)")
    parser.add_argument("--format", dest="fmt", choices=["txt", "json"], default="json")
    parser.add_argument("--disable-algorithms", action="store_true", help="Skip deterministic algorithm scoring")
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
        result = build_result_with_options(args.text, use_algorithms=not args.disable_algorithms)
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
