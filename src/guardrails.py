"""
Fail-closed guardrails for RAG answers.

The generator may still hallucinate. The final answer must either be grounded in
retrieved evidence, replaced with an extractive snippet, or abstain.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Sequence

from .analyzer import AnalysisResult
from .generator import INSUFFICIENT_EVIDENCE_ANSWER, extractive_fallback


ABSTAIN_ANSWER = INSUFFICIENT_EVIDENCE_ANSWER


@dataclass
class GuardrailDecision:
    status: str
    reason: str
    original_hallucinated: bool
    final_hallucinated: bool
    fallback_used: bool

    def to_dict(self) -> dict:
        return asdict(self)


AnalyzerFn = Callable[[str], AnalysisResult]


def _is_safe(analysis: AnalysisResult) -> bool:
    if analysis.label == "abstained":
        return True
    if analysis.hallucinated:
        return False
    if analysis.reliability == "low":
        return False
    if analysis.context_overlap is not None and analysis.context_overlap < 0.35:
        return False
    if analysis.grounded_ratio is not None and analysis.grounded_ratio < 0.50:
        return False
    return True


def guard_answer(
    query: str,
    passages: Sequence[str],
    candidate_answer: str,
    candidate_analysis: AnalysisResult,
    analyze: AnalyzerFn,
) -> tuple[str, AnalysisResult, GuardrailDecision]:
    if _is_safe(candidate_analysis):
        return (
            candidate_answer,
            candidate_analysis,
            GuardrailDecision(
                status="accepted",
                reason="Generated answer passed grounding checks.",
                original_hallucinated=False,
                final_hallucinated=False,
                fallback_used=False,
            ),
        )

    fallback = extractive_fallback(query, passages, max_chars=900)
    if fallback.strip():
        fallback_analysis = analyze(fallback)
        if _is_safe(fallback_analysis):
            return (
                fallback,
                fallback_analysis,
                GuardrailDecision(
                    status="replaced",
                    reason="Generated answer was unsafe, so the system returned an extractive evidence span.",
                    original_hallucinated=candidate_analysis.hallucinated,
                    final_hallucinated=False,
                    fallback_used=True,
                ),
            )

    abstain_analysis = AnalysisResult(
        label="abstained",
        hallucinated=False,
        reliability="high",
        explanation="The system abstained because the generated answer and fallback were not safely grounded.",
        per_sentence_notes=[],
        entailment_probs_mean=None,
        contradiction_probs_mean=None,
        context_overlap=1.0,
        grounded_ratio=1.0,
        unsupported_numbers=[],
        unsupported_entities=[],
    )
    return (
        ABSTAIN_ANSWER,
        abstain_analysis,
        GuardrailDecision(
            status="abstained",
            reason="Generated answer was unsafe and no reliable extractive fallback was available.",
            original_hallucinated=candidate_analysis.hallucinated,
            final_hallucinated=False,
            fallback_used=False,
        ),
    )
