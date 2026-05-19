"""NLI entailment verifier for the final HALT-RAG pipeline.

The verifier is separate from answer generation. It prefers a HuggingFace NLI
model and falls back to conservative lexical checks when the model cannot be
loaded locally.
"""

from __future__ import annotations

import re
import os
from functools import lru_cache
from typing import Any

import numpy as np


PREFERRED_MODEL = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
FALLBACK_MODEL = "roberta-large-mnli"
LABELS = ("entailment", "neutral", "contradiction")
NEGATIONS = {
    "not",
    "no",
    "never",
    "cannot",
    "can't",
    "isn't",
    "aren't",
    "wasn't",
    "weren't",
    "doesn't",
    "don't",
    "didn't",
}


def predict_entailment(premise: str, hypothesis: str) -> dict[str, float | str]:
    """Return entailment, neutral, contradiction, and the top label."""
    premise = str(premise or "")
    hypothesis = str(hypothesis or "")
    if not premise.strip() or not hypothesis.strip():
        return _with_label(entailment=0.05, neutral=0.70, contradiction=0.25)

    bundle = _load_nli_bundle()
    if bundle is not None:
        try:
            tokenizer, model, device = bundle
            import torch
            import torch.nn.functional as functional

            encoded = tokenizer(
                premise[:3000],
                hypothesis[:800],
                return_tensors="pt",
                truncation=True,
                max_length=512,
            )
            encoded = {key: value.to(device) for key, value in encoded.items()}
            with torch.no_grad():
                logits = model(**encoded).logits
                probs = functional.softmax(logits, dim=-1)[0].detach().cpu().numpy()

            mapped = _map_model_probabilities(model, probs)
            return _with_label(**mapped)
        except Exception:
            pass

    return _fallback_entailment(premise, hypothesis)


@lru_cache(maxsize=1)
def _load_nli_bundle():
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        device = "cuda" if torch.cuda.is_available() else "cpu"
        local_only = os.getenv("HALT_RAG_ALLOW_MODEL_DOWNLOAD", "0").lower() not in {
            "1",
            "true",
            "yes",
        }
        for model_name in (PREFERRED_MODEL, FALLBACK_MODEL):
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=local_only)
                model = AutoModelForSequenceClassification.from_pretrained(model_name, local_files_only=local_only)
                model.to(device)
                model.eval()
                return tokenizer, model, device
            except Exception:
                continue
    except Exception:
        return None
    return None


def _map_model_probabilities(model: Any, probs: np.ndarray) -> dict[str, float]:
    labels = getattr(getattr(model, "config", None), "id2label", {}) or {}
    mapped = {"entailment": 0.0, "neutral": 0.0, "contradiction": 0.0}

    for idx, prob in enumerate(probs):
        label = str(labels.get(idx, "")).lower()
        if "entail" in label:
            mapped["entailment"] = float(prob)
        elif "neutral" in label:
            mapped["neutral"] = float(prob)
        elif "contrad" in label:
            mapped["contradiction"] = float(prob)

    if sum(mapped.values()) == 0.0 and len(probs) >= 3:
        # Common MNLI ordering for RoBERTa: contradiction, neutral, entailment.
        mapped = {
            "contradiction": float(probs[0]),
            "neutral": float(probs[1]),
            "entailment": float(probs[2]),
        }
    return mapped


def _fallback_entailment(premise: str, hypothesis: str) -> dict[str, float | str]:
    premise_tokens = set(_tokens(premise))
    hypothesis_tokens = set(_tokens(hypothesis))
    if not hypothesis_tokens:
        return _with_label(entailment=0.05, neutral=0.85, contradiction=0.10)

    containment = len(premise_tokens & hypothesis_tokens) / len(hypothesis_tokens)
    contradiction = 0.10
    if _has_negation_mismatch(premise, hypothesis) or _has_number_mismatch(premise, hypothesis):
        contradiction = 0.70

    if contradiction >= 0.65:
        entailment = min(0.20, containment * 0.35)
        neutral = max(0.05, 1.0 - contradiction - entailment)
    elif containment >= 0.75:
        entailment = 0.78
        neutral = 0.17
    elif containment >= 0.45:
        entailment = 0.45
        neutral = 0.45
    else:
        entailment = 0.15
        neutral = 0.72

    total = entailment + neutral + contradiction
    return _with_label(
        entailment=entailment / total,
        neutral=neutral / total,
        contradiction=contradiction / total,
    )


def _with_label(entailment: float, neutral: float, contradiction: float) -> dict[str, float | str]:
    scores = {
        "entailment": _clamp(entailment),
        "neutral": _clamp(neutral),
        "contradiction": _clamp(contradiction),
    }
    total = sum(scores.values())
    if total > 0.0:
        scores = {key: value / total for key, value in scores.items()}
    label = max(scores, key=scores.get)
    return {**{key: round(value, 4) for key, value in scores.items()}, "label": label}


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?", text.lower())


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\b\d+(?:\.\d+)?%?\b", text))


def _has_number_mismatch(premise: str, hypothesis: str) -> bool:
    hypothesis_numbers = _numbers(hypothesis)
    if not hypothesis_numbers:
        return False
    return bool(hypothesis_numbers - _numbers(premise))


def _has_negation_mismatch(premise: str, hypothesis: str) -> bool:
    premise_words = set(_tokens(premise))
    hypothesis_words = set(_tokens(hypothesis))
    shared_content = (premise_words & hypothesis_words) - NEGATIONS
    if len(shared_content) < 3:
        return False
    return bool(premise_words & NEGATIONS) != bool(hypothesis_words & NEGATIONS)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
