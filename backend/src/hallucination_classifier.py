from __future__ import annotations
import re
from typing import Any

REASONING_MARKERS = {
    "therefore",
    "thus",
    "hence",
    "consequently",
    "because",
    "since",
    "implies",
    "suggests",
    "means",
    "indicates",
    "results in",
    "leads to",
}

def classify_hallucination(
    answer: str,
    sentence_results: list[dict[str, Any]],
    retrieved_contexts: list[dict[str, Any]],
) -> dict[str, str]:
    total = max(1, len(sentence_results))
    grounded = sum(1 for item in sentence_results if item.get("label") == "grounded")
    hallucinated = [item for item in sentence_results if item.get("label") == "hallucinated"]
    uncertain = [item for item in sentence_results if item.get("label") == "uncertain"]
    avg_retrieval = _avg([float(item.get("score", 0.0) or 0.0) for item in retrieved_contexts])
    avg_grounding = _avg([float(item.get("grounding_score", 0.0) or 0.0) for item in sentence_results])
    avg_semantic = _avg([float(item.get("semantic_similarity", 0.0) or 0.0) for item in sentence_results])
    avg_overlap = _avg([float(item.get("overlap_score", 0.0) or 0.0) for item in sentence_results])
    max_contradiction = max(
        [float(item.get("contradiction_score", 0.0) or 0.0) for item in sentence_results] or [0.0]
    )

    if grounded / total >= 0.70 and not hallucinated:
        return {
            "risk": "low" if avg_grounding >= 0.70 else "medium",
            "hallucination_type": "faithful",
            "explanation": "Most answer sentences are grounded in retrieved context.",
        }

    retrieval_irrelevant = avg_semantic < 0.25 and avg_overlap < 0.25 and avg_grounding < 0.45
    if not retrieved_contexts or avg_retrieval < 0.20 or retrieval_irrelevant:
        return {
            "risk": "high",
            "hallucination_type": "contextual",
            "explanation": "Retrieved context is missing or weak, so the answer is not reliably grounded.",
        }

    unsupported_text = " ".join(item.get("sentence", "") for item in hallucinated + uncertain)

    if _has_reasoning_marker(answer) and avg_grounding < 0.70 and max_contradiction < 0.65:
        return {
            "risk": "medium" if not hallucinated else "high",
            "hallucination_type": "reasoning",
            "explanation": "Relevant context exists, but the conclusion is not strongly entailed.",
        }

    if max_contradiction >= 0.55 or _has_factual_claim(unsupported_text):
        return {
            "risk": "high" if hallucinated else "medium",
            "hallucination_type": "factual",
            "explanation": "The answer contains unsupported factual, numeric, date, or entity claims.",
        }

    return {
        "risk": "medium" if hallucinated or uncertain else "low",
        "hallucination_type": "contextual",
        "explanation": "Some claims are not clearly supported by the retrieved context.",
    }


def _has_factual_claim(text: str) -> bool:
    if re.search(r"\b\d{2,4}(?:\.\d+)?%?\b", text):
        return True
    if re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b", text):
        return True
    # Capitalized entity-like tokens away from sentence start are a useful weak signal.
    return len(re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)) >= 2


def _has_reasoning_marker(text: str) -> bool:
    lowered = (text or "").lower()
    return any(marker in lowered for marker in REASONING_MARKERS)


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
