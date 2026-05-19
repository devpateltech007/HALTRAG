from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

from src.deep_hallucination_detector import analyze_answer, lexical_overlap
from src.models.embedding_model import cosine_similarity, encode_query
from src.models.nli_model import predict_entailment


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = PROJECT_ROOT / "data" / "eval" / "halt_rag_eval.csv"
RESULTS_DIR = PROJECT_ROOT / "results"


def run_ablation(eval_path: str | Path = EVAL_PATH) -> pd.DataFrame:
    data = pd.read_csv(eval_path)
    rows = []
    for variant in ["similarity only", "NLI only", "similarity + overlap", "full detector"]:
        expected = []
        predicted = []
        for _, row in data.iterrows():
            expected_label = row["expected_sentence_label"]
            expected.append(expected_label)
            predicted.append(_predict_variant(variant, row))

        hallucinated_true = [label == "hallucinated" for label in expected]
        hallucinated_pred = [label == "hallucinated" for label in predicted]
        rows.append(
            {
                "variant": variant,
                "sentence_label_accuracy": round(float(accuracy_score(expected, predicted)), 4),
                "hallucinated_f1": round(float(f1_score(hallucinated_true, hallucinated_pred, zero_division=0)), 4),
            }
        )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output = pd.DataFrame(rows)
    output.to_csv(RESULTS_DIR / "ablation_results.csv", index=False)
    return output


def _predict_variant(variant: str, row) -> str:
    context = str(row["context"])
    answer = str(row["generated_answer"])
    if variant == "full detector":
        result = analyze_answer(
            row["question"],
            answer,
            [{"source_id": row["id"], "text": context, "score": 0.85, "verified": True}],
        )
        return result[0]["label"] if result else "hallucinated"

    if variant == "similarity only":
        score = float(cosine_similarity(encode_query(answer), encode_query(context)))
        return _label(score)

    if variant == "NLI only":
        nli = predict_entailment(context, answer)
        if float(nli["contradiction"]) >= 0.60:
            return "hallucinated"
        return _label(float(nli["entailment"]))

    similarity = float(cosine_similarity(encode_query(answer), encode_query(context)))
    overlap = lexical_overlap(answer, context)
    return _label((0.60 * similarity) + (0.40 * overlap))


def _label(score: float) -> str:
    if score >= 0.70:
        return "grounded"
    if score >= 0.40:
        return "uncertain"
    return "hallucinated"


if __name__ == "__main__":
    print(run_ablation().to_string(index=False))

