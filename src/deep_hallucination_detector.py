from __future__ import annotations
import re
from typing import Any

import numpy as np

from src.models.embedding_model import cosine_similarity, encode_query, encode_texts
from src.models.nli_model import predict_entailment


GROUNDING_THRESHOLD = 0.70
HALLUCINATION_THRESHOLD = 0.40
STRONG_ENTAILMENT = 0.55
HIGH_CONTRADICTION = 0.60


def analyze_answer(
    question: str,
    answer: str,
    retrieved_contexts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return sentence-level grounding analysis."""
    del question  # Reserved for future question-aware calibration.
    sentences = split_sentences(answer)
    contexts = _normalize_contexts(retrieved_contexts)

    if not sentences:
        return []
    if not contexts:
        return [_missing_context_result(sentence) for sentence in sentences]

    context_texts = [context["text"] for context in contexts]
    context_embeddings = encode_texts(context_texts)
    results = []

    for sentence in sentences:
        sentence_embedding = encode_query(sentence)
        similarities = cosine_similarity(sentence_embedding, context_embeddings)
        scores = np.asarray(similarities).reshape(-1)
        best_idx = int(np.argmax(scores)) if len(scores) else 0
        best_context = contexts[best_idx]
        semantic_similarity = _clamp(float(scores[best_idx])) if len(scores) else 0.0

        nli = predict_entailment(best_context["text"], sentence)
        entailment_score = float(nli["entailment"])
        contradiction_score = float(nli["contradiction"])
        overlap_score = lexical_overlap(sentence, best_context["text"])
        grounding_score = (
            0.50 * entailment_score
            + 0.30 * semantic_similarity
            + 0.20 * overlap_score
        )

        if contradiction_score >= HIGH_CONTRADICTION or grounding_score < HALLUCINATION_THRESHOLD:
            label = "hallucinated"
        elif grounding_score >= GROUNDING_THRESHOLD and entailment_score >= STRONG_ENTAILMENT:
            label = "grounded"
        else:
            label = "uncertain"

        results.append(
            {
                "sentence": sentence,
                "label": label,
                "best_context": best_context["text"],
                "semantic_similarity": round(semantic_similarity, 4),
                "entailment_score": round(entailment_score, 4),
                "contradiction_score": round(contradiction_score, 4),
                "overlap_score": round(overlap_score, 4),
                "grounding_score": round(_clamp(grounding_score), 4),
                "source_id": best_context.get("source_id"),
            }
        )

    return results


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text or "") if len(part.strip()) > 2]


def lexical_overlap(sentence: str, context: str) -> float:
    sentence_tokens = set(_tokens(sentence))
    context_tokens = set(_tokens(context))
    if not sentence_tokens:
        return 0.0
    return len(sentence_tokens & context_tokens) / len(sentence_tokens)


def average_grounding_score(sentence_results: list[dict[str, Any]]) -> float:
    if not sentence_results:
        return 0.0
    return round(
        sum(float(item.get("grounding_score", item.get("score", 0.0))) for item in sentence_results)
        / len(sentence_results),
        4,
    )


def _missing_context_result(sentence: str) -> dict[str, Any]:
    return {
        "sentence": sentence,
        "label": "hallucinated",
        "best_context": "",
        "semantic_similarity": 0.0,
        "entailment_score": 0.0,
        "contradiction_score": 0.0,
        "overlap_score": 0.0,
        "grounding_score": 0.0,
        "source_id": None,
    }


def _normalize_contexts(contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for idx, context in enumerate(contexts or []):
        text = str(context.get("text") or context.get("content") or "").strip()
        if not text:
            continue
        normalized.append(
            {
                "source_id": context.get("source_id") or context.get("id") or f"context_{idx + 1}",
                "text": text,
                "score": float(context.get("score", 0.0) or 0.0),
            }
        )
    return normalized


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?", (text or "").lower())


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))

