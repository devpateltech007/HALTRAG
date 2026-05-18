"""
Smoke evaluation: retrieval Recall@k on hand-labeled queries for sample_corpus.json,
optional toy check against heuristic EXAMPLES in hallucination_label_sketch.py.

Usage (from repo root):
    python scripts/evaluate.py
    python scripts/evaluate.py path/to/corpus.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.retriever import BM25Retriever  # noqa: E402


# Fallback cases if the custom question file is unavailable.
DEFAULT_RETRIEVAL_CASES = [
    ("What is metformin used for?", {"med_001"}),
    ("What are the elements of medical malpractice?", {"legal_002"}),
    ("How does warfarin interact with other drugs?", {"med_003"}),
    ("What is the FDA drug approval process?", {"legal_004"}),
]


def recall_hit(retriever: BM25Retriever, query: str, expected: set[str], k: int) -> float:
    hits = retriever.retrieve(query, top_k=k)
    got = {r.doc_id for r in hits}
    return 1.0 if expected & got else 0.0


def load_hallucination_sketch_module():
    path = ROOT / "experiments" / "hallucination_label_sketch.py"
    spec = importlib.util.spec_from_file_location("hallucination_label_sketch", path)
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def expected_label(example_name: str) -> str:
    n = example_name.lower()
    if "grounded" in n:
        return "grounded"
    if "factual" in n:
        return "factual"
    if "contextual" in n:
        return "contextual"
    if "reasoning" in n:
        return "reasoning"
    if "faithfulness" in n:
        return "faithfulness"
    return ""


def load_retrieval_cases(path: Path) -> list[tuple[str, set[str]]]:
    if not path.is_file():
        return DEFAULT_RETRIEVAL_CASES
    data = json.loads(path.read_text(encoding="utf-8"))
    cases: list[tuple[str, set[str]]] = []
    for row in data:
        question = str(row.get("question", "")).strip()
        expected = {str(doc_id) for doc_id in row.get("expected_doc_ids", [])}
        if question and expected:
            cases.append((question, expected))
    return cases or DEFAULT_RETRIEVAL_CASES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate retrieval and heuristic hallucination checks.")
    parser.add_argument("corpus", nargs="?", default=str(ROOT / "data" / "sample_corpus.json"))
    parser.add_argument(
        "--questions",
        default=str(ROOT / "data" / "custom_50_questions.json"),
        help="Custom QA JSON with question and expected_doc_ids fields.",
    )
    args = parser.parse_args(argv[1:] if argv else None)

    corp_path = Path(args.corpus)
    question_path = Path(args.questions)

    if not corp_path.is_file():
        print(f"Corpus not found: {corp_path}", file=sys.stderr)
        return 1

    retriever = BM25Retriever.from_json(str(corp_path))
    retrieval_cases = load_retrieval_cases(question_path)

    ks = [1, 3, 5]
    print(f"Corpus: {corp_path} ({len(retriever.corpus_rows)} docs)")
    print(f"Questions: {question_path} ({len(retrieval_cases)} cases)")
    print("Retrieval macro hit-rate (any expected doc in top-k):")
    for k in ks:
        scores = [recall_hit(retriever, q, exp, k) for q, exp in retrieval_cases]
        print(f"  @{k}: {sum(scores) / len(scores):.3f}")

    try:
        sketch = load_hallucination_sketch_module()
        hits = total = 0
        for ex in sketch.EXAMPLES:
            gold = expected_label(ex["name"])
            if not gold:
                continue
            total += 1
            pred, _ = sketch.classify_hallucination(ex["context"], ex["answer"])
            if pred == gold:
                hits += 1
        if total > 0:
            print("\nHeuristic hallucination EXAMPLES (substring-based gold from names):")
            print(f"  agreement: {hits}/{total}")
    except Exception as exc:  # noqa: BLE001 — smoke script helper
        print("\n(heuristic EXAMPLES check skipped:", exc, ")")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
