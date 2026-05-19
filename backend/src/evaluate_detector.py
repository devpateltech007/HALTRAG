from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from src.confidence import compute_confidence
from src.deep_hallucination_detector import analyze_answer
from src.detector_validation import validate_detector_signals
from src.hallucination_classifier import classify_hallucination


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = PROJECT_ROOT / "data" / "eval" / "halt_rag_eval.csv"
RESULTS_DIR = PROJECT_ROOT / "results"


def evaluate(eval_path: str | Path = EVAL_PATH) -> dict[str, Any]:
    rows = pd.read_csv(eval_path)
    y_sentence_true = []
    y_sentence_pred = []
    y_type_true = []
    y_type_pred = []
    confidences = []
    predictions = []

    for _, row in rows.iterrows():
        context = {
            "source_id": row["id"],
            "text": row["context"],
            "score": 0.85,
            "verified": True,
            "metadata": {"domain": row["domain"], "eval": True},
        }
        sentence_results = analyze_answer(row["question"], row["generated_answer"], [context])
        detector_signals = validate_detector_signals(sentence_results, [0.85])
        classification = classify_hallucination(row["generated_answer"], sentence_results, [context])
        confidence = compute_confidence(
            retrieval_scores=[0.85],
            sentence_results=sentence_results,
            detector_signals=detector_signals,
        )

        predicted_sentence_label = sentence_results[0]["label"] if sentence_results else "hallucinated"
        predicted_type = classification["hallucination_type"]

        y_sentence_true.append(row["expected_sentence_label"])
        y_sentence_pred.append(predicted_sentence_label)
        y_type_true.append(row["expected_hallucination_type"])
        y_type_pred.append(predicted_type)
        confidences.append(confidence)
        predictions.append(
            {
                "id": row["id"],
                "expected_sentence_label": row["expected_sentence_label"],
                "predicted_sentence_label": predicted_sentence_label,
                "expected_hallucination_type": row["expected_hallucination_type"],
                "predicted_hallucination_type": predicted_type,
                "confidence": confidence,
                "detector_signals": detector_signals,
            }
        )

    hallucinated_true = [label == "hallucinated" for label in y_sentence_true]
    hallucinated_pred = [label == "hallucinated" for label in y_sentence_pred]
    precision, recall, f1, _ = precision_recall_fscore_support(
        hallucinated_true,
        hallucinated_pred,
        average="binary",
        zero_division=0,
    )

    report = {
        "rows": int(len(rows)),
        "sentence_label_accuracy": round(float(accuracy_score(y_sentence_true, y_sentence_pred)), 4),
        "hallucination_type_accuracy": round(float(accuracy_score(y_type_true, y_type_pred)), 4),
        "hallucinated_precision": round(float(precision), 4),
        "hallucinated_recall": round(float(recall), 4),
        "hallucinated_f1": round(float(f1), 4),
        "confidence_distribution": {
            "min": round(float(min(confidences) if confidences else 0.0), 4),
            "max": round(float(max(confidences) if confidences else 0.0), 4),
            "mean": round(float(sum(confidences) / len(confidences) if confidences else 0.0), 4),
        },
        "predictions": predictions,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "evaluation_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _save_plots(y_sentence_true, y_sentence_pred, y_type_pred, confidences)
    return report


def _save_plots(
    y_sentence_true: list[str],
    y_sentence_pred: list[str],
    y_type_pred: list[str],
    confidences: list[float],
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    labels = ["grounded", "uncertain", "hallucinated"]
    matrix = confusion_matrix(y_sentence_true, y_sentence_pred, labels=labels)
    plt.figure(figsize=(6, 5))
    sns.heatmap(matrix, annot=True, fmt="d", xticklabels=labels, yticklabels=labels, cmap="Blues")
    plt.xlabel("Predicted")
    plt.ylabel("Expected")
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "confusion_matrix.png")
    plt.close()

    plt.figure(figsize=(7, 4))
    pd.Series(y_type_pred).value_counts().reindex(
        ["faithful", "factual", "contextual", "reasoning"], fill_value=0
    ).plot(kind="bar", color="#2563eb")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "type_distribution.png")
    plt.close()

    plt.figure(figsize=(7, 4))
    plt.hist(confidences, bins=10, color="#059669", edgecolor="white")
    plt.xlabel("Trust confidence")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "confidence_distribution.png")
    plt.close()


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))

