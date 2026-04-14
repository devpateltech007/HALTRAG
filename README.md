# HALT-RAG: Hallucination Analysis and Localization with Typing for RAG

## Overview

HALT-RAG is a Retrieval-Augmented Generation (RAG) system designed for **high-stakes question answering** in domains like medicine and law, where hallucinated answers can have serious consequences. The project focuses on building a pipeline that retrieves relevant evidence, generates grounded answers, and classifies hallucinations into fine-grained categories—factual, contextual, reasoning, and faithfulness errors.

This repository represents the **start of implementation**. We are currently in the early experimentation and architecture design phase.

## Problem Statement

Large language models frequently hallucinate—they produce answers that sound confident but are factually wrong, unsupported by the retrieved context, or logically inconsistent. In general-purpose QA this is annoying; in **medical and legal QA** it can be dangerous.

Existing hallucination detection methods often treat the problem as binary (hallucinated vs. not). We want to go further and **categorize** hallucinations so that downstream systems or human reviewers can understand *what kind* of error occurred and *where* it originated in the pipeline.

## Why This Matters

- A medical chatbot that fabricates drug interactions could harm patients.
- A legal QA tool that invents case precedents could mislead attorneys and judges.
- Fine-grained hallucination typing helps build trust and enables targeted fixes.

## Team

| Name | SJSU ID | GitHub |
|------|---------|--------|
| Dev Patel | — | @dev-patel |
| Kenil Vaghasiya | — | @kenil-vaghasiya |

## Project Goals

1. Build a modular RAG pipeline (retriever → generator → hallucination analyzer).
2. Implement a hallucination **typing** system that classifies errors into categories:
   - **Factual** — generated claim contradicts world knowledge.
   - **Contextual** — answer is not grounded in the retrieved passages.
   - **Reasoning** — logical steps in the answer are invalid.
   - **Faithfulness** — answer distorts or misrepresents the source text.
3. Evaluate on medical and legal QA benchmarks.
4. Provide interpretable explanations of detected hallucinations.

## Datasets Under Exploration

| Dataset | Domain | Why we're looking at it |
|---------|--------|------------------------|
| **PubMedQA** | Biomedical | Real medical research questions with yes/no/maybe answers and supporting context. |
| **TriviaQA** | Open-domain | Large-scale QA with evidence documents; good for retrieval baselines. |
| **HotpotQA** | Multi-hop | Requires reasoning over multiple documents; useful for reasoning-type hallucinations. |
| **QASPER** | Scientific papers | Question answering over NLP papers; tests long-document retrieval. |

We have not committed to a final dataset yet. See [`docs/dataset_notes.md`](docs/dataset_notes.md) for detailed notes.

## Planned Approach

```
Query → Retriever (BM25 / dense) → Top-k Passages → Generator (LLM) → Answer
                                                                         │
                                                         Hallucination Analyzer
                                                                         │
                                                         Type label + Explanation
```

1. **Retrieval**: Start with BM25 (lexical), then move to dense retrieval (e.g., Contriever, ColBERT).
2. **Generation**: Use an open-source LLM (e.g., Llama-3, Mistral) to produce answers conditioned on retrieved passages.
3. **Hallucination Detection & Typing**: Combine NLI-based entailment checking, entity overlap heuristics, and possibly a fine-tuned classifier to label hallucination categories.
4. **Evaluation**: Measure retrieval recall, answer quality (F1 / ROUGE), and hallucination detection accuracy.

More detail is in [`docs/architecture.md`](docs/architecture.md).

## What Has Been Done So Far

- [x] Formed team and brainstormed project ideas
- [x] Surveyed related work on RAG hallucinations
- [x] Decided on hallucination taxonomy (factual / contextual / reasoning / faithfulness)
- [x] Explored and compared candidate datasets
- [x] Designed high-level architecture
- [x] Created a sample corpus for local testing
- [x] Implemented a simple BM25-style baseline retriever
- [x] Wrote an exploratory hallucination labeling sketch using heuristics

## Current Status

We are in the **early implementation** stage. The retriever baseline works on sample data with token overlap scoring. The hallucination labeling sketch is a heuristic prototype—no ML models are trained yet. We have not integrated a generator LLM into the pipeline.

## Repository Structure

```
HALT-RAG/
├── README.md                              # This file
├── requirements.txt                       # Minimal Python dependencies
├── .gitignore                             # Standard ignores
├── data/
│   ├── README.md                          # Data documentation
│   └── sample_corpus.json                 # Tiny sample corpus for testing
├── experiments/
│   ├── baseline_retrieval.py              # Simple lexical retrieval baseline
│   └── hallucination_label_sketch.py      # Heuristic hallucination labeling prototype
├── notebooks/
│   └── initial_experiments.md             # Lab notes from early experiments
└── docs/
    ├── architecture.md                    # System design / pipeline plan
    ├── dataset_notes.md                   # Dataset research notes
    ├── progress_log.md                    # Dated progress log
    └── team_work_split.md                 # Contribution tracking
```

## How to Run

### Setup

```bash
# Clone the repository
git clone https://github.com/<your-org>/halt-rag.git
cd halt-rag

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run the baseline retrieval experiment

```bash
python experiments/baseline_retrieval.py
```

This loads `data/sample_corpus.json`, takes a hard-coded test query, scores documents by token overlap, and prints the ranked results.

### Run the hallucination labeling sketch

```bash
python experiments/hallucination_label_sketch.py
```

This runs a few hand-crafted examples through simple heuristic rules and prints the predicted hallucination type for each.

## Next Steps

- [ ] Integrate a proper BM25 implementation (e.g., via `rank_bm25`)
- [ ] Download and preprocess PubMedQA and/or HotpotQA
- [ ] Add a generator component using an open-source LLM
- [ ] Replace heuristic labeling with NLI-based entailment checking
- [ ] Build an end-to-end pipeline prototype
- [ ] Design evaluation metrics and run initial benchmarks
- [ ] Experiment with dense retrieval models

## Challenges and Limitations

- **No gold hallucination labels**: Most QA datasets don't label *why* an answer is wrong, only *whether* it is. We may need to create or adapt annotations.
- **Compute constraints**: Running large LLMs locally is expensive; we'll likely rely on smaller models or API access.
- **Subjectivity in typing**: The boundary between "contextual" and "faithfulness" hallucinations can be blurry. We need clear annotation guidelines.
- **Early stage**: The current code is exploratory. The heuristic labeler is not a real detector—it's a sketch to test our category definitions.

## References

1. Lewis, P., et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS 2020.
2. Ji, Z., et al. "Survey of Hallucination in Natural Language Generation." ACM Computing Surveys, 2023.
3. Manakul, P., et al. "SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models." EMNLP 2023.
4. Min, S., et al. "FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation." EMNLP 2023.
5. PubMedQA: Jin, Q., et al. "PubMedQA: A Dataset for Biomedical Research Question Answering." EMNLP 2019.
6. HotpotQA: Yang, Z., et al. "HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering." EMNLP 2018.
7. TriviaQA: Joshi, M., et al. "TriviaQA: A Large Scale Distantly Supervised Challenge Dataset for Reading Comprehension." ACL 2017.
8. QASPER: Dasigi, P., et al. "A Dataset of Information-Seeking Questions and Answers Anchored in Research Papers." NAACL 2021.
<<<<<<< HEAD

=======
>>>>>>> ec4ab144e81e83435f581ccbf0f13400c07ecc77
