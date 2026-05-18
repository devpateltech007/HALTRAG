"""
Answer generator: FLAN-T5 (optional) with extractive fallback when torch/transformers are unavailable.
"""

from __future__ import annotations

import re
from typing import List, Sequence

STOPWORDS_FALLBACK = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "for", "on", "with", "at", "by", "and", "or", "but",
    "what", "who", "when", "where", "why", "how", "does", "do", "did", "can",
    "could", "should", "would", "which", "name", "list",
}

INSUFFICIENT_EVIDENCE_ANSWER = "Not enough evidence in context."


def tokenize_overlap(text: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS_FALLBACK]


def extractive_fallback(
    query: str,
    passages: Sequence[str],
    max_chars: int = 600,
    min_overlap: int = 1,
    min_query_coverage: float = 0.34,
) -> str:
    """Pick the passage that overlaps most with the query tokens; return a trimmed excerpt."""
    q_tokens = set(tokenize_overlap(query))
    if not q_tokens or not passages:
        return ""

    best_p, best_score = passages[0], -1.0
    for p in passages:
        if not (p or "").strip():
            continue
        dtoks = set(tokenize_overlap(p))
        overlap = len(q_tokens & dtoks)
        if overlap > best_score:
            best_score = overlap
            best_p = p

    query_coverage = best_score / max(len(q_tokens), 1)
    if best_score < min_overlap or query_coverage < min_query_coverage:
        return ""

    text = (best_p or "").strip().replace("\n", " ")
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "..."


def build_prompt(question: str, context_block: str) -> str:
    return (
        "Answer strictly using ONLY the Context below. If the Context does not support an answer, "
        'say "Not enough evidence in context."\n\n'
        f"Context:\n{context_block}\n\nQuestion: {question}\n\nAnswer:"
    )


DEFAULT_GEN_MODEL = "google/flan-t5-small"

_gen_cache: dict[str, tuple] = {}


def _get_seq2seq(model_name: str, device_str: str):
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    if model_name not in _gen_cache:
        tok = AutoTokenizer.from_pretrained(model_name)
        dev = torch.device(device_str)
        mdl = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(dev)
        mdl.eval()
        _gen_cache[model_name] = (tok, mdl, dev)
    return _gen_cache[model_name]


def generate_answer(
    question: str,
    context_block: str,
    *,
    model_name: str = DEFAULT_GEN_MODEL,
    max_new_tokens: int = 128,
) -> tuple[str, str]:
    """
    Returns (answer, mode_tag) where mode_tag is \"seq2seq\" or \"extractive_fallback\" or \"missing_deps\".
    """
    passages = [b.strip() for b in context_block.split("\n\n") if b.strip()]
    prompt = build_prompt(question, context_block)

    try:
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    except ImportError:
        ans = extractive_fallback(question, passages)
        return (ans if ans else INSUFFICIENT_EVIDENCE_ANSWER, "missing_deps")

    import torch

    device_str = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer, model, device = _get_seq2seq(model_name, device_str)

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=1024,
    ).to(device)
    with torch.no_grad():
        out_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            num_beams=4,
            do_sample=False,
        )
    decoded = tokenizer.decode(out_ids[0], skip_special_tokens=True).strip()
    if decoded:
        return decoded, "seq2seq"
    ans = extractive_fallback(question, passages)
    return ans if ans else INSUFFICIENT_EVIDENCE_ANSWER, "extractive_fallback"
