from __future__ import annotations
from statistics import mean, pstdev
from typing import Any


def validate_detector_signals(
    sentence_results: list[dict[str, Any]],
    retrieval_scores: list[float],
) -> dict[str, Any]:
    """Estimate how much independent signals agree with detector output."""
    retrieval_strength = _avg([_clamp(score) for score in retrieval_scores])
    if not sentence_results:
        return {
            "detector_confidence": 0.15,
            "agreement_level": "low",
            "signal_disagreement": True,
            "explanation": (
                "No sentence-level evidence was available. This is a low-confidence "
                "detector signal, not a certainty claim."
            ),
        }

    per_sentence_confidences = []
    disagreements = 0

    for item in sentence_results:
        signals = [
            float(item.get("entailment_score", 0.0) or 0.0),
            float(item.get("semantic_similarity", 0.0) or 0.0),
            float(item.get("overlap_score", 0.0) or 0.0),
            retrieval_strength,
        ]
        signal_mean = mean(signals)
        signal_spread = pstdev(signals)
        per_sentence_confidences.append(_clamp(signal_mean * (1.0 - min(signal_spread, 0.50))))

        binary = [value >= 0.50 for value in signals]
        if any(binary) and not all(binary):
            disagreements += 1

    confidence = _avg(per_sentence_confidences)
    disagreement_ratio = disagreements / len(sentence_results)
    signal_disagreement = disagreement_ratio >= 0.35
    if signal_disagreement:
        confidence *= 0.75

    if confidence >= 0.70 and not signal_disagreement:
        agreement_level = "high"
    elif confidence >= 0.45:
        agreement_level = "medium"
    else:
        agreement_level = "low"

    return {
        "detector_confidence": round(_clamp(confidence), 4),
        "agreement_level": agreement_level,
        "signal_disagreement": bool(signal_disagreement),
        "explanation": (
            "Detector confidence is estimated from agreement among NLI entailment, "
            "semantic similarity, lexical overlap, and retrieval strength. It is "
            "probabilistic and should not be treated as proof of truth."
        ),
    }


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))

