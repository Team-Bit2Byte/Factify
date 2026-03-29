"""
Shared fake news prediction utilities for Factify.

This module loads the shipped `.keras` weights archive and performs manual
NumPy inference for the simple Embedding -> LSTM -> Dense(sigmoid) model.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

import h5py
import numpy as np

from src.ml.algorithms.universal_facts import (
    detect_universal_fact_contradictions,
    detect_verified_universal_facts,
)

MODEL_PATH = Path(__file__).with_name("fake_news_detector.keras")
VOCAB_SIZE = 5000
SEQUENCE_LENGTH = 42
REPUTABLE_SOURCES = {
    "reuters",
    "associated press",
    "ap",
    "bbc",
    "npr",
    "the guardian",
    "new york times",
    "washington post",
    "times of india",
    "hindustan times",
}

_TOKEN_RE = re.compile(r"[a-z0-9']+")
_MODEL_CACHE: dict | None = None


@dataclass
class DetectionResult:
    verdict: str
    verdict_label: str
    raw_score: float
    fake_probability: int
    original_probability: int
    confidence: str
    confidence_score: int
    summary: str
    findings: List[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _load_model_weights() -> dict:
    global _MODEL_CACHE

    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    with zipfile.ZipFile(MODEL_PATH) as archive:
        config = json.loads(archive.read("config.json"))
        weights_data = archive.read("model.weights.h5")

    build_shape = config["config"].get("build_input_shape") or [None, SEQUENCE_LENGTH]
    sequence_length = int(build_shape[1])

    with h5py.File(io.BytesIO(weights_data), "r") as weights:
        _MODEL_CACHE = {
            "sequence_length": sequence_length,
            "embedding": weights["layers/embedding/vars/0"][()],
            "lstm_kernel": weights["layers/lstm/cell/vars/0"][()],
            "lstm_recurrent": weights["layers/lstm/cell/vars/1"][()],
            "lstm_bias": weights["layers/lstm/cell/vars/2"][()],
            "dense_kernel": weights["layers/dense/vars/0"][()],
            "dense_bias": weights["layers/dense/vars/1"][()],
        }

    return _MODEL_CACHE


def _hash_token(token: str) -> int:
    digest = hashlib.md5(token.encode("utf-8")).hexdigest()
    return (int(digest, 16) % (VOCAB_SIZE - 1)) + 1


def _vectorize_text(text: str, max_length: int) -> np.ndarray:
    normalized_tokens = _TOKEN_RE.findall((text or "").lower())
    token_ids = [_hash_token(token) for token in normalized_tokens]
    token_ids = token_ids[-max_length:]

    padded = np.zeros(max_length, dtype=np.int32)
    if token_ids:
        padded[-len(token_ids):] = token_ids
    return padded


def _run_lstm(sequence_embeddings: np.ndarray, model: dict) -> float:
    units = model["lstm_recurrent"].shape[0]
    h_t = np.zeros(units, dtype=np.float32)
    c_t = np.zeros(units, dtype=np.float32)

    kernel = model["lstm_kernel"]
    recurrent = model["lstm_recurrent"]
    bias = model["lstm_bias"]

    for step in sequence_embeddings:
        z = step @ kernel + h_t @ recurrent + bias
        z0, z1, z2, z3 = np.split(z, 4)
        i_t = _sigmoid(z0)
        f_t = _sigmoid(z1)
        g_t = np.tanh(z2)
        o_t = _sigmoid(z3)
        c_t = f_t * c_t + i_t * g_t
        h_t = o_t * np.tanh(c_t)

    dense = h_t @ model["dense_kernel"] + model["dense_bias"]
    probability = float(_sigmoid(dense)[0])
    return max(0.0, min(1.0, probability))


def predict_fake_probability(text: str) -> float:
    model = _load_model_weights()
    token_ids = _vectorize_text(text, model["sequence_length"])
    embeddings = model["embedding"][token_ids]
    return _run_lstm(embeddings, model)


def _heuristic_risk(text: str, suspicious_elements: List[str], source: str) -> float:
    lowered_source = (source or "").strip().lower()
    word_count = len((text or "").split())
    # Start with neutral baseline instead of fixed 0.15
    risk = 0.0

    # Suspicious elements are strong signals
    risk += min(0.5, len(suspicious_elements) * 0.22)

    # Word count adjustments - more nuanced
    if word_count < 15:
        risk += 0.18
    elif word_count < 30:
        risk += 0.08
    elif word_count > 150:
        risk -= 0.06

    # Source credibility has significant impact
    if not lowered_source or lowered_source == "none" or lowered_source in {"user provided text", "unknown source"}:
        risk += 0.08  # Reduced penalty for unknown source
    elif any(name in lowered_source for name in REPUTABLE_SOURCES):
        risk -= 0.25  # Stronger bonus for reputable sources
    else:
        risk += 0.03

    return max(0.0, min(1.0, risk))


def classify_text(text: str, suspicious_elements: List[str] | None = None, source: str = "") -> DetectionResult:
    suspicious_elements = suspicious_elements or []
    raw_score = predict_fake_probability(text)
    heuristic_score = _heuristic_risk(text, suspicious_elements, source)
    
    # The LSTM model has learned spurious patterns and can't be fully trusted
    # Weight the heuristics more heavily (70%) vs ML model (30%)
    # This prevents the model from incorrectly flagging credible news
    calibrated_score = (raw_score * 0.30) + (heuristic_score * 0.70)
    lowered_source = (source or "").strip().lower()
    word_count = len((text or "").split())

    if any(name in lowered_source for name in REPUTABLE_SOURCES) and not suspicious_elements and word_count >= 8:
        calibrated_score = min(calibrated_score, 0.30)
    elif (not lowered_source or lowered_source == "none") and len(suspicious_elements) >= 2 and word_count < 30:
        calibrated_score = max(calibrated_score, 0.72)

    fake_probability = int(round(calibrated_score * 100))
    original_probability = 100 - fake_probability
    distance_from_center = abs(calibrated_score - 0.5) * 2.0
    confidence_score = int(round(distance_from_center * 100))

    if confidence_score >= 70:
        confidence = "high"
    elif confidence_score >= 40:
        confidence = "medium"
    else:
        confidence = "low"

    if calibrated_score >= 0.67:
        verdict = "likely_fake_false"
        verdict_label = "Likely Fake / False"
        summary = "The model sees strong overlap with misinformation-like language patterns."
    elif calibrated_score <= 0.33:
        verdict = "likely_original"
        verdict_label = "Likely Original"
        summary = "The model sees stronger signals of a legitimate or grounded report."
    else:
        verdict = "unverified"
        verdict_label = "Unverified"
        summary = "The signal is mixed, so this content should not be treated as verified yet."

    findings: List[str] = []
    if suspicious_elements:
        findings.extend(suspicious_elements[:3])

    text_length = len((text or "").split())
    if text_length < 40:
        findings.append("Limited text was available, which reduces verification confidence.")
    elif text_length > 250:
        findings.append("The prediction used a truncated sequence window because the model input length is capped.")

    if source and source != "None":
        findings.append(f"Source detected: {source}.")
    else:
        findings.append("No clearly identified source was found in the analyzed content.")

    if verdict == "likely_fake_false" and not suspicious_elements:
        findings.append("The model score alone pushed this item into the high-risk range.")
    elif verdict == "likely_original" and not suspicious_elements:
        findings.append("No major heuristic warning signs were detected alongside the model score.")
    elif verdict == "unverified":
        findings.append("The result sits near the model boundary, so manual checking is still recommended.")

    unique_findings = list(dict.fromkeys(findings))

    return DetectionResult(
        verdict=verdict,
        verdict_label=verdict_label,
        raw_score=round(raw_score, 4),
        fake_probability=fake_probability,
        original_probability=original_probability,
        confidence=confidence,
        confidence_score=confidence_score,
        summary=summary,
        findings=unique_findings[:4],
    )


def classify_with_algorithm_score(
    text: str,
    algorithm_score: float,
    suspicious_elements: List[str] | None = None,
    source: str = "",
) -> DetectionResult:
    base = classify_text(text, suspicious_elements, source)
    algorithm_fake_probability = int(round(100 - max(0.0, min(100.0, algorithm_score))))
    # Trust the deterministic algorithm much more than the flawed LSTM model
    # Algorithm: 70%, Base (which already blends LSTM+heuristic): 30%
    blended_fake_probability = int(round((base.fake_probability * 0.30) + (algorithm_fake_probability * 0.70)))
    blended_original_probability = 100 - blended_fake_probability
    confidence_score = int(round((base.confidence_score * 0.4) + (abs(algorithm_score - 50.0) * 1.2)))

    if confidence_score >= 70:
        confidence = "high"
    elif confidence_score >= 40:
        confidence = "medium"
    else:
        confidence = "low"

    if blended_fake_probability >= 67:
        verdict = "likely_fake_false"
        verdict_label = "Likely Fake / False"
        summary = "The model and deterministic credibility checks both point toward a high-risk article."
    elif blended_fake_probability <= 33:
        verdict = "likely_original"
        verdict_label = "Likely Original"
        summary = "The model and deterministic credibility checks both lean toward legitimate reporting."
    else:
        verdict = "unverified"
        verdict_label = "Unverified"
        summary = "The model and deterministic checks disagree or remain too close to call."

    return DetectionResult(
        verdict=verdict,
        verdict_label=verdict_label,
        raw_score=base.raw_score,
        fake_probability=blended_fake_probability,
        original_probability=blended_original_probability,
        confidence=confidence,
        confidence_score=min(confidence_score, 100),
        summary=summary,
        findings=base.findings,
    )


def classify_with_algorithm_assessment(
    text: str,
    algorithm_assessment: dict,
    suspicious_elements: List[str] | None = None,
    source: str = "",
) -> DetectionResult:
    suspicious_elements = suspicious_elements or []
    base = classify_with_algorithm_score(
        text,
        float(algorithm_assessment.get("overall_score") or 0.0),
        suspicious_elements,
        source,
    )

    algorithm_score = float(algorithm_assessment.get("overall_score") or 0.0)
    algorithm_verdict = algorithm_assessment.get("verdict")
    claim_flags = algorithm_assessment.get("claim_flags") or []
    contradiction_flags = [flag for flag in claim_flags if "factual contradiction" in flag.lower()]
    verified_fact_hits = detect_verified_universal_facts(text)
    contradiction_hits = contradiction_flags or detect_universal_fact_contradictions(text)

    if contradiction_hits:
        findings = list(dict.fromkeys(base.findings + contradiction_hits[:2]))
        return DetectionResult(
            verdict="likely_fake_false",
            verdict_label="Likely Fake / False",
            raw_score=base.raw_score,
            fake_probability=max(base.fake_probability, 82),
            original_probability=100 - max(base.fake_probability, 82),
            confidence="high",
            confidence_score=max(base.confidence_score, 72),
            summary="The claim matches a known factual contradiction, so it is pushed into the high-risk band.",
            findings=findings[:5],
        )

    if verified_fact_hits:
        findings = list(dict.fromkeys(base.findings + ["Claim matches a verified universal fact pattern."]))
        return DetectionResult(
            verdict="likely_original",
            verdict_label="Likely Original",
            raw_score=base.raw_score,
            fake_probability=min(base.fake_probability, 24),
            original_probability=max(base.original_probability, 76),
            confidence="high",
            confidence_score=max(base.confidence_score, 72),
            summary="The claim matches a verified universal fact pattern and is promoted into the low-risk band.",
            findings=findings[:5],
        )

    if algorithm_verdict == "likely_original" and algorithm_score >= 92.0:
        findings = list(dict.fromkeys(base.findings + ["Deterministic credibility checks strongly support a grounded report."]))
        return DetectionResult(
            verdict="likely_original",
            verdict_label="Likely Original",
            raw_score=base.raw_score,
            fake_probability=min(base.fake_probability, 28),
            original_probability=max(base.original_probability, 72),
            confidence="high" if base.confidence_score >= 60 else "medium",
            confidence_score=max(base.confidence_score, 68),
            summary="Strong deterministic credibility signals outweigh the weaker model-side uncertainty for this report.",
            findings=findings[:5],
        )

    if algorithm_verdict == "likely_fake_false" and algorithm_score <= 45.0:
        findings = list(dict.fromkeys(base.findings + claim_flags[:2]))
        boosted_fake_probability = max(base.fake_probability, 72)
        return DetectionResult(
            verdict="likely_fake_false",
            verdict_label="Likely Fake / False",
            raw_score=base.raw_score,
            fake_probability=boosted_fake_probability,
            original_probability=100 - boosted_fake_probability,
            confidence="high" if base.confidence_score >= 60 else "medium",
            confidence_score=max(base.confidence_score, 64),
            summary="Deterministic credibility checks point strongly toward a high-risk or misleading claim.",
            findings=findings[:5],
        )

    return base
