"""
Hallucination typing: DistilRoBERTa MNLI (optional) + lightweight heuristics.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import List, Sequence, Tuple

NEGATION_WORDS = {
    "not", "no", "never", "neither", "nor", "cannot",
    "doesn't", "don't", "won't", "isn't", "aren't",
    "wasn't", "weren't", "hasn't", "haven't",
    "doesn", "don", "won", "isn", "aren", "wasn",
    "weren", "hasn", "haven", "cant",
}
EXAGGERATION_WORDS = {
    "always", "never", "all", "every", "none", "absolutely",
    "certainly", "definitely", "guaranteed", "impossible",
    "completely", "totally", "entirely",
}

COVERAGE_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "it", "in", "of",
    "to", "and", "for", "on", "with", "that", "this", "by",
    "as", "at", "from", "or", "be", "been", "being", "has", "had",
    "have", "its", "their", "they", "them", "he", "she", "we", "you",
}

ABSTENTION_PATTERNS = (
    "not enough evidence",
    "insufficient evidence",
    "insufficient context",
    "i don't know",
    "i do not know",
    "cannot answer",
    "can't answer",
    "no answer in context",
)

ENTITY_IGNORE = {
    "The", "This", "That", "These", "Those", "Answer", "Context", "Question",
    "Not", "No", "There", "It", "In", "For", "If", "When", "Current",
}

# Public three-way NLI classifier (contradiction / neutral / entailment).
DEFAULT_NLI_MODEL = "microsoft/deberta-base-mnli"


def split_sentences(text: str) -> List[str]:
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p.strip()]
    return parts if parts else ([text.strip()] if text.strip() else [])


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def is_abstention(answer: str) -> bool:
    low = answer.lower()
    return any(pattern in low for pattern in ABSTENTION_PATTERNS)


def content_tokens(text: str) -> List[str]:
    return [
        t
        for t in tokenize(text)
        if t not in COVERAGE_STOPWORDS and t not in NEGATION_WORDS and len(t) > 1
    ]


def negation_mismatch(context: str, answer: str) -> bool:
    context_sentences = split_sentences(context)
    answer_sentences = split_sentences(answer)
    if not context_sentences or not answer_sentences:
        return False

    for ans in answer_sentences:
        ans_content = set(content_tokens(ans))
        if not ans_content:
            continue

        best_context = ""
        best_ratio = 0.0
        best_overlap = 0
        for ctx in context_sentences:
            ctx_content = set(content_tokens(ctx))
            overlap = len(ans_content & ctx_content)
            ratio = overlap / max(len(ans_content), 1)
            if ratio > best_ratio or overlap > best_overlap:
                best_context = ctx
                best_ratio = ratio
                best_overlap = overlap

        if best_overlap < 2 or best_ratio < 0.25:
            continue

        ctx_neg = set(tokenize(best_context)) & NEGATION_WORDS
        ans_neg = set(tokenize(ans)) & NEGATION_WORDS
        if ctx_neg != ans_neg:
            return True
    return False


def sentence_grounding(context: str, answer: str) -> tuple[float, List[str]]:
    context_sentences = split_sentences(context)
    answer_sentences = split_sentences(answer)
    if not answer_sentences:
        return 0.0, []
    if not context_sentences:
        return 0.0, ["No retrieved context was available."]

    notes: List[str] = []
    grounded = 0
    for ans in answer_sentences:
        ans_content = set(content_tokens(ans))
        if not ans_content:
            grounded += 1
            notes.append(f"\"{ans[:80]}\" has no unsupported content words.")
            continue

        best_ratio = 0.0
        for ctx in context_sentences:
            ctx_content = set(content_tokens(ctx))
            ratio = len(ans_content & ctx_content) / max(len(ans_content), 1)
            best_ratio = max(best_ratio, ratio)
        if best_ratio >= 0.45:
            grounded += 1
        notes.append(
            f"\"{ans[:80]}{'...' if len(ans) > 80 else ''}\" "
            f"lexical grounding~{best_ratio:.2f}"
        )

    return grounded / len(answer_sentences), notes


def unsupported_fact_signals(context: str, answer: str) -> tuple[List[str], List[str]]:
    context_lower = context.lower()
    answer_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", answer))
    context_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", context))
    unsupported_numbers = sorted(answer_numbers - context_numbers)

    answer_entities = {
        ent
        for ent in re.findall(r"\b[A-Z][A-Za-z0-9-]{2,}\b", answer)
        if ent not in ENTITY_IGNORE
    }
    unsupported_entities = sorted(
        ent for ent in answer_entities if ent.lower() not in context_lower
    )
    return unsupported_numbers, unsupported_entities[:8]


def token_coverage(context: str, answer: str) -> float:
    ans_tokens = content_tokens(answer)
    if not ans_tokens:
        return 1.0
    ctx_tokens = set(tokenize(context))
    return sum(1 for t in ans_tokens if t in ctx_tokens) / len(ans_tokens)


def exaggeration_score(answer: str) -> float:
    ans_tokens = tokenize(answer)
    if not ans_tokens:
        return 0.0
    return sum(1 for t in ans_tokens if t in EXAGGERATION_WORDS) / len(ans_tokens)


def softmax(logits):
    mx = max(logits)
    exps = [math.exp(x - mx) for x in logits]
    s = sum(exps)
    return [e / s for e in exps]


@dataclass
class AnalysisResult:
    label: str
    hallucinated: bool
    reliability: str
    explanation: str
    per_sentence_notes: List[str]
    entailment_probs_mean: float | None
    contradiction_probs_mean: float | None
    context_overlap: float | None = None
    grounded_ratio: float | None = None
    unsupported_numbers: List[str] | None = None
    unsupported_entities: List[str] | None = None


def _heuristic_aggregate(context: str, answer: str) -> AnalysisResult:
    if is_abstention(answer):
        return AnalysisResult(
            label="abstained",
            hallucinated=False,
            reliability="high",
            explanation="The system abstained because retrieved context did not support a safe answer.",
            per_sentence_notes=[],
            entailment_probs_mean=None,
            contradiction_probs_mean=None,
            context_overlap=1.0,
            grounded_ratio=1.0,
            unsupported_numbers=[],
            unsupported_entities=[],
        )

    cov = token_coverage(context, answer)
    grounded_ratio, notes = sentence_grounding(context, answer)
    unsupported_numbers, unsupported_entities = unsupported_fact_signals(context, answer)
    neg_flip = negation_mismatch(context, answer)
    exagg = exaggeration_score(answer)
    has_unsupported = bool(unsupported_numbers or len(unsupported_entities) > 2)

    if neg_flip:
        return AnalysisResult(
            label="reasoning",
            hallucinated=True,
            reliability="low",
            explanation=(
                "Answer polarity/negation does not align with context - weak or invalid inference."
            ),
            per_sentence_notes=notes,
            entailment_probs_mean=None,
            contradiction_probs_mean=None,
            context_overlap=cov,
            grounded_ratio=grounded_ratio,
            unsupported_numbers=unsupported_numbers,
            unsupported_entities=unsupported_entities,
        )
    if has_unsupported and (cov < 0.65 or grounded_ratio < 0.75):
        return AnalysisResult(
            label="factual",
            hallucinated=True,
            reliability="low",
            explanation=(
                "The answer introduces numbers or named entities that are not supported by retrieved context."
            ),
            per_sentence_notes=notes,
            entailment_probs_mean=None,
            contradiction_probs_mean=None,
            context_overlap=cov,
            grounded_ratio=grounded_ratio,
            unsupported_numbers=unsupported_numbers,
            unsupported_entities=unsupported_entities,
        )
    if grounded_ratio < 0.45 and len(answer) > 30:
        return AnalysisResult(
            label="contextual",
            hallucinated=True,
            reliability="low",
            explanation=f"Low sentence grounding against retrieved context (grounded_ratio~{grounded_ratio:.2f}).",
            per_sentence_notes=notes,
            entailment_probs_mean=None,
            contradiction_probs_mean=None,
            context_overlap=cov,
            grounded_ratio=grounded_ratio,
            unsupported_numbers=unsupported_numbers,
            unsupported_entities=unsupported_entities,
        )
    if cov < 0.35 and len(answer) > 30:
        return AnalysisResult(
            label="contextual",
            hallucinated=True,
            reliability="low",
            explanation=f"Low lexical overlap between answer and retrieved context (coverage~{cov:.2f}).",
            per_sentence_notes=notes,
            entailment_probs_mean=None,
            contradiction_probs_mean=None,
            context_overlap=cov,
            grounded_ratio=grounded_ratio,
            unsupported_numbers=unsupported_numbers,
            unsupported_entities=unsupported_entities,
        )
    if exagg > 0.04:
        return AnalysisResult(
            label="faithfulness",
            hallucinated=True,
            reliability="medium",
            explanation=(
                "Strong absolutist wording relative to cautious context - possible meaning distortion."
            ),
            per_sentence_notes=notes,
            entailment_probs_mean=None,
            contradiction_probs_mean=None,
            context_overlap=cov,
            grounded_ratio=grounded_ratio,
            unsupported_numbers=unsupported_numbers,
            unsupported_entities=unsupported_entities,
        )
    return AnalysisResult(
        label="grounded",
        hallucinated=False,
        reliability="high",
        explanation="Heuristic checks passed; validate with larger evidence and NLI when available.",
        per_sentence_notes=notes,
        entailment_probs_mean=None,
        contradiction_probs_mean=None,
        context_overlap=cov,
        grounded_ratio=grounded_ratio,
        unsupported_numbers=unsupported_numbers,
        unsupported_entities=unsupported_entities,
    )


_nli_models: dict[str, tuple] = {}


def _get_nli(model_name: str):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    if model_name not in _nli_models:
        tok = AutoTokenizer.from_pretrained(model_name)
        mdl = AutoModelForSequenceClassification.from_pretrained(model_name)
        mdl.eval()
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        mdl.to(device)
        _nli_models[model_name] = (tok, mdl, device)
    return _nli_models[model_name]


def _prob_buckets(id2label: dict, probs_list: List[float]) -> tuple[float, float, float]:
    pe = pn = pc = 0.0
    for idx, p in enumerate(probs_list):
        key = idx
        if key not in id2label:
            continue
        n = str(id2label[key]).lower()
        if "entail" in n:
            pe += p
        elif "neutral" in n:
            pn += p
        elif "contrad" in n:
            pc += p
    return pe, pn, pc


def _nli_classify_pairs(
    premises: Sequence[str],
    hypotheses: Sequence[str],
    model_name: str,
) -> List[Tuple[str, float, float, float]]:
    """
    For each premise-hypothesis pair, return (predicted_label, p_entail, p_neutral, p_contradict).
    """
    import torch

    tokenizer, model, device = _get_nli(model_name)

    raw_id2label = dict(model.config.id2label)
    id2label: dict[int, str] = {}
    for k, v in raw_id2label.items():
        try:
            id2label[int(k)] = str(v)
        except (TypeError, ValueError):
            continue

    out: List[Tuple[str, float, float, float]] = []
    for prem, hyp in zip(premises, hypotheses):
        enc = tokenizer(
            prem,
            hyp,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        ).to(device)
        with torch.no_grad():
            logits = model(**enc).logits.squeeze(0)
        vec = logits if logits.dim() == 1 else logits[0]
        probs_list = softmax(vec.detach().tolist())
        pe, pn, pc = _prob_buckets(id2label, probs_list)
        pred_idx = int(max(range(len(probs_list)), key=lambda i: probs_list[i]))
        pred = str(id2label[int(pred_idx)])
        out.append((pred, pe, pn, pc))
    return out


def _nli_one_pair(
    premise: str, hypothesis: str, model_name: str
) -> Tuple[str, float, float, float]:
    return _nli_classify_pairs([premise], [hypothesis], model_name)[0]


def _split_retrieval_blocks(context_block: str, max_chars: int = 2200) -> List[str]:
    parts = [p.strip() for p in context_block.split("\n\n") if p.strip()]
    if len(parts) <= 1:
        return [context_block.strip()[:max_chars]]
    return [p[:max_chars] for p in parts]


def analyze_answer(
    question: str,
    retrieved_passages_concat: str,
    answer: str,
    *,
    use_nli: bool = True,
    nli_model: str = DEFAULT_NLI_MODEL,
) -> AnalysisResult:
    """Classify hallucination type and summarize reliability."""

    sentences = split_sentences(answer)
    if not sentences or not answer.strip():
        return AnalysisResult(
            label="contextual",
            hallucinated=True,
            reliability="low",
            explanation="Empty or non-informative answer.",
            per_sentence_notes=[],
            entailment_probs_mean=None,
            contradiction_probs_mean=None,
        )

    if is_abstention(answer):
        return _heuristic_aggregate(retrieved_passages_concat, answer)

    cov = token_coverage(retrieved_passages_concat, answer)
    grounded_ratio, grounding_notes = sentence_grounding(retrieved_passages_concat, answer)
    unsupported_numbers, unsupported_entities = unsupported_fact_signals(
        retrieved_passages_concat,
        answer,
    )

    if not use_nli:
        return _heuristic_aggregate(retrieved_passages_concat, answer)

    try:
        prem = retrieved_passages_concat.strip()
        if len(prem) < 15:
            return _heuristic_aggregate(retrieved_passages_concat, answer)

        blocks = _split_retrieval_blocks(prem)
        sentence_notes: List[str] = []
        best_ent_per_sent: List[float] = []
        max_contrad_per_sent: List[float] = []

        for sent in sentences:
            best_ent = 0.0
            contra_at_aligned = 0.0
            pn_at_best_ent = 0.0

            hyp = sent[:384]
            for block in blocks:
                bk = block[:2800]
                if not bk.strip():
                    continue
                _, pe, pn, pc = _nli_one_pair(bk, hyp, nli_model)
                # Keep contradiction for the SAME passage that best supports the span (avoid
                # unrelated-doc "contradiction" dominating the signal).
                if pe >= best_ent:
                    best_ent = pe
                    pn_at_best_ent = pn
                    contra_at_aligned = pc

            best_ent_per_sent.append(best_ent)
            max_contrad_per_sent.append(contra_at_aligned)
            sentence_notes.append(
                f"\"{sent[:80]}{'...' if len(sent) > 80 else ''}\" "
                f"(best entail across passages~{best_ent:.2f}, "
                f"contradiction at best-aligned passage~{contra_at_aligned:.2f}, "
                f"neutral at best-aligned passage~{pn_at_best_ent:.2f})"
            )

        avg_e = sum(best_ent_per_sent) / max(len(best_ent_per_sent), 1)
        aligned_c_mean = (
            sum(max_contrad_per_sent) / max(len(max_contrad_per_sent), 1)
            if max_contrad_per_sent
            else 0.0
        )
        peak_c = max(max_contrad_per_sent) if max_contrad_per_sent else 0.0
        has_unsupported = bool(unsupported_numbers or len(unsupported_entities) > 2)

        if has_unsupported and (avg_e < 0.55 or grounded_ratio < 0.75):
            lbl = "factual"
            expl = "The answer includes unsupported numbers or named entities in addition to weak support signals."
            hall = True
            rel = "low"
        elif peak_c >= 0.40 or aligned_c_mean >= 0.32:
            lbl = "factual"
            expl = (
                "At least one answer span is contradictory to retrieved context under NLI scores "
                f"(peak aligned-contradiction prob~{peak_c:.2f})."
            )
            hall = True
            rel = "low"
        elif negation_mismatch(retrieved_passages_concat, answer):
            lbl = "reasoning"
            expl = "NLI signals are mixed; answer negation polarity diverges from context."
            hall = True
            rel = "medium"
        elif exaggeration_score(answer) > 0.04 and avg_e > 0.35:
            lbl = "faithfulness"
            expl = (
                "Context largely supports wording, but absolutist tone may overstretch claims."
            )
            hall = True
            rel = "medium"
        elif avg_e < 0.30:
            lbl = "contextual"
            expl = (
                "Limited entailment between answer spans and retrieved passages - "
                "answer may be ungrounded."
            )
            hall = True
            rel = "low"
        elif avg_e >= 0.40 and peak_c < 0.20:
            lbl = "grounded"
            expl = (
                "Answer spans align with at least one retrieved passage under NLI "
                f"(mean best entail~{avg_e:.2f})."
            )
            hall = False
            rel = "high"
        else:
            lbl = "contextual"
            expl = "Ambiguous NLI signals; treat answer as lightly supported until verified."
            hall = True
            rel = "medium"

        return AnalysisResult(
            label=lbl,
            hallucinated=hall,
            reliability=rel,
            explanation=expl,
            per_sentence_notes=sentence_notes or grounding_notes,
            entailment_probs_mean=avg_e,
            contradiction_probs_mean=peak_c,
            context_overlap=cov,
            grounded_ratio=grounded_ratio,
            unsupported_numbers=unsupported_numbers,
            unsupported_entities=unsupported_entities,
        )

    except Exception:
        return _heuristic_aggregate(retrieved_passages_concat, answer)
