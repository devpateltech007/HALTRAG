"""
End-to-end HALT-RAG: retrieve → generate → hallucination analyze.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from typing import Any, List, Sequence

from .analyzer import AnalysisResult, analyze_answer
from .generator import DEFAULT_GEN_MODEL, INSUFFICIENT_EVIDENCE_ANSWER, extractive_fallback, generate_answer
from .guardrails import GuardrailDecision, guard_answer
from .retriever import BM25Retriever, RetrievedDoc


@dataclass
class PipelineResult:
    query: str
    retrieved: List[dict[str, Any]]
    context_block: str
    answer: str
    generation_mode: str
    analysis: dict[str, Any]
    raw_answer: str
    raw_analysis: dict[str, Any]
    guardrail: dict[str, Any]


def format_retrieved(retrieved: Sequence[RetrievedDoc]) -> List[dict[str, Any]]:
    return [
        {
            "id": r.doc_id,
            "score": round(r.score, 4),
            "title": r.title,
            "text_preview": (r.text[:200] + "...") if len(r.text) > 200 else r.text,
            "domain": r.domain,
        }
        for r in retrieved
    ]


def run_pipeline(
    query: str,
    corpus_path: str,
    *,
    top_k: int = 5,
    no_llm: bool = False,
    skip_nli: bool = False,
    generator_model: str = DEFAULT_GEN_MODEL,
    max_new_tokens: int = 128,
    guard: bool = True,
) -> PipelineResult:
    retriever = BM25Retriever.from_json(corpus_path)
    retrieved = retriever.retrieve(query, top_k=top_k)
    context_block = retriever.passages_for_prompt(retrieved)

    passages = [r.text for r in retrieved]
    title_blob = "\n".join(r.title + "\n" + r.text for r in retrieved)

    if no_llm:
        answer = extractive_fallback(query, passages)
        answer = answer or extractive_fallback(query, title_blob.split("\n"))
        generation_mode = "extractive_fallback"
        if not answer.strip():
            answer = INSUFFICIENT_EVIDENCE_ANSWER
            generation_mode = "extractive_abstain"
    else:
        answer, generation_mode = generate_answer(
            query,
            context_block,
            model_name=generator_model,
            max_new_tokens=max_new_tokens,
        )

    raw_answer = answer
    raw_analysis_obj: AnalysisResult = analyze_answer(
        query,
        context_block,
        raw_answer,
        use_nli=not skip_nli,
    )

    if guard:
        def analyze_final(candidate: str) -> AnalysisResult:
            return analyze_answer(
                query,
                context_block,
                candidate,
                use_nli=not skip_nli,
            )

        final_answer, analysis_obj, guardrail_obj = guard_answer(
            query,
            passages,
            raw_answer,
            raw_analysis_obj,
            analyze_final,
        )
        answer = final_answer
        if guardrail_obj.status == "replaced":
            generation_mode = f"{generation_mode}_guarded_extractive"
        elif guardrail_obj.status == "abstained":
            generation_mode = f"{generation_mode}_guarded_abstain"
    else:
        analysis_obj = raw_analysis_obj
        guardrail_obj = GuardrailDecision(
            status="disabled",
            reason="Guardrail was disabled by caller.",
            original_hallucinated=raw_analysis_obj.hallucinated,
            final_hallucinated=raw_analysis_obj.hallucinated,
            fallback_used=False,
        )

    analysis = asdict(analysis_obj)

    return PipelineResult(
        query=query,
        retrieved=format_retrieved(retrieved),
        context_block=context_block,
        answer=answer,
        generation_mode=generation_mode,
        analysis=analysis,
        raw_answer=raw_answer,
        raw_analysis=asdict(raw_analysis_obj),
        guardrail=asdict(guardrail_obj),
    )


def main(argv: list[str] | None = None) -> int:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    default_corpus = os.path.join(root, "data", "sample_corpus.json")

    parser = argparse.ArgumentParser(description="HALT-RAG end-to-end pipeline")
    parser.add_argument("--query", type=str, help="Question to answer")
    parser.add_argument("--corpus", type=str, default=default_corpus, help="Path to corpus JSON")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--no-llm", action="store_true", help="Skip FLAN-T5; use extractive fallback")
    parser.add_argument("--skip-nli", action="store_true", help="Skip NLI model; use heuristics only")
    parser.add_argument("--generator-model", type=str, default=DEFAULT_GEN_MODEL)
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--no-guard", action="store_true", help="Return raw generator output without fail-closed guard")
    parser.add_argument("--json", dest="json_out", action="store_true", help="Print JSON only")
    args = parser.parse_args(argv)

    if not args.query:
        parser.error("--query is required")

    if not os.path.isfile(args.corpus):
        parser.error(f"Corpus not found: {args.corpus}")

    result = run_pipeline(
        args.query,
        args.corpus,
        top_k=args.top_k,
        no_llm=args.no_llm,
        skip_nli=args.skip_nli,
        generator_model=args.generator_model,
        max_new_tokens=args.max_new_tokens,
        guard=not args.no_guard,
    )

    if args.json_out:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        return 0

    print(f"Query: {result.query}\n")
    print("Retrieved (top-ranked):")
    for r in result.retrieved:
        print(f"  [{r['id']}] score={r['score']} — {r['title']}")
    print("\nGeneration mode:", result.generation_mode)
    print("Guardrail:", result.guardrail["status"], "-", result.guardrail["reason"])
    print("\nAnswer:\n", result.answer, "\n", sep="")
    a = result.analysis
    print("Hallucination / reliability:")
    print(f"  Type:       {a['label']}")
    print(f"  Reliable:   {a['reliability']}")
    print(f"  Hallucinat: {a['hallucinated']}")
    print(f"  Explain:    {a['explanation']}")
    if a.get("entailment_probs_mean") is not None:
        print(
            "  NLI avg:    entail="
            f"{a['entailment_probs_mean']:.3f}, contradiction="
            f"{a['contradiction_probs_mean']:.3f}",
        )
    if a.get("per_sentence_notes"):
        print("\n  Per sentence:")
        for ln in a["per_sentence_notes"]:
            print(f"    - {ln}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
