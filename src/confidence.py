from __future__ import annotations
from typing import Any


def compute_confidence(
    retrieved_contexts: list[dict[str, Any]] | None = None,
    sentence_analysis: list[dict[str, Any]] | None = None,
    detector_validation: dict[str, Any] | None = None,
    model_agreement_score: float | None = None,
    retrieval_scores: list[float] | None = None,
    sentence_results: list[dict[str, Any]] | None = None,
    detector_signals: dict[str, Any] | None = None,
) -> float:
    """Compute trust score from retrieval, sentence grounding, and detector confidence.

    The first three keyword arguments preserve compatibility with the legacy
    prototype. The final three are the clean final pipeline inputs.
    """
    del model_agreement_score
    contexts = retrieved_contexts or []
    sentences = sentence_results if sentence_results is not None else (sentence_analysis or [])
    validation = detector_signals if detector_signals is not None else (detector_validation or {})

    if retrieval_scores is None:
        retrieval_scores = [
            _safe_float(context.get("score"), 0.0)
            for context in contexts
            if isinstance(context, dict)
        ]

    avg_retrieval = _average([_normalize_retrieval_score(score) for score in retrieval_scores])
    avg_grounding = _average(
        [
            _safe_float(item.get("grounding_score", item.get("score")), 0.0)
            for item in sentences
            if isinstance(item, dict)
        ]
    )
    detector_confidence = _safe_float(validation.get("detector_confidence"), 0.0)

    score = (0.30 * avg_retrieval) + (0.45 * avg_grounding) + (0.25 * detector_confidence)
    return round(_clamp(score), 4)


def hallucination_risk(confidence: float, hallucination_type: str = "faithful") -> str:
    """Convert calibrated confidence into a demo-friendly risk bucket."""
    confidence = _clamp(confidence)
    if hallucination_type != "faithful" and confidence < 0.70:
        return "high" if confidence < 0.45 else "medium"
    if confidence >= 0.75:
        return "low"
    if confidence >= 0.45:
        return "medium"
    return "high"


def _normalize_retrieval_score(score: float) -> float:
    score = float(score)
    if score < 0.0:
        return 0.0
    if score <= 1.0:
        return score
    return score / (score + 1.0)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
