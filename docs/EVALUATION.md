# HALT-RAG Evaluation

This part explains how we tested the hallucination detector in HALT-RAG.

The detector is not meant to be a perfect yes or no checker. Instead, it gives a trust score that helps us understand whether an answer is probably grounded, uncertain, or hallucinated.

The main goals of the evaluation are:

1. Show that the detector does better than random guessing when separating grounded answers from hallucinated ones.
2. Show that all four signals are useful. If we remove NLI, similarity, overlap, or retrieval strength, the detector should perform worse.

## Evaluation dataset

We use the file:

```bash
data/eval/halt_rag_eval.csv
````

It has 40 hand-made test cases.

These cases cover the four answer types:

* faithful
* factual
* contextual
* reasoning

They also include examples from the medical and legal demo domains.

Each row includes the question, answer, gold context, expected hallucination type, expected risk bucket, and notes.

## Running the detector evaluation

To run the evaluation:

```bash
python -m src.evaluate_detector
```

This creates a few files in the `results/` folder:

```bash
results/evaluation_report.json
results/confusion_matrix.png
results/type_distribution.png
results/confidence_distribution.png
```

The JSON report has the detector scores for each example, the predicted labels, the expected labels, accuracy, and macro F1.

The images make it easier to see how well the detector is doing. For example, the confusion matrix shows where the detector got things right or mixed up grounded, uncertain, and hallucinated answers.

## Ablation study

To run the ablation test:

```bash
python -m src.ablation
```

This creates:

```bash
results/ablation_results.csv
```

The ablation test removes one signal at a time and checks how much the score drops.

This helps answer an important question: “Is the detector only relying on one signal?”

In our case, the goal is to show that it is not. NLI, similarity, overlap, and retrieval strength all help. When any one of them is removed, the detector should perform worse.

## Metrics we report

We report:

* accuracy for sentence-level grounding labels
* macro F1 across grounded, uncertain, and hallucinated labels
* detector agreement rate, which means how often all four signals agree
* confidence distribution, which shows how confident the detector is on correct vs. incorrect predictions
* latency, which is the end-to-end response time saved in:

```bash
logs/audit.jsonl
```

## Live verification

After starting the backend and frontend, we can test the demo manually.

Example flow:

1. Ask:

```text
What does HIPAA protect?
```

This should return grounded sentences and low risk.

2. Ask something that is not supported by the corpus.

This should return uncertain or hallucinated labels with lower confidence.

3. Add a verified question and answer on the `/admin` page.

Then ask the same question again. The answer should become grounded after the update.

4. Open the `/logs` page and filter by:

```text
risk = high
```

This shows the traces that were flagged as risky.

## Why this matters

This evaluation shows that HALT-RAG is not just guessing. It uses multiple signals to estimate whether an answer is trustworthy. It also shows that no single signal is carrying the whole system, which makes the detector harder to fool.
