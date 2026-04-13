# HALT-RAG — Architecture & Design Notes

*Last updated: April 2026*

## High-Level Pipeline

```
                         ┌─────────────┐
                         │  User Query │
                         └──────┬──────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │   Retriever Module   │
                     │  (BM25 → Dense)      │
                     └──────────┬──────────┘
                                │  top-k passages
                                ▼
                     ┌─────────────────────┐
                     │  Generator Module    │
                     │  (LLM: Llama / etc.) │
                     └──────────┬──────────┘
                                │  generated answer
                                ▼
                     ┌─────────────────────┐
                     │  Hallucination       │
                     │  Analyzer Module     │
                     └──────────┬──────────┘
                                │
                        ┌───────┴────────┐
                        ▼                ▼
                  Type Label       Explanation
              (factual, context,   (which claim is
               reasoning, faith.)  unsupported & why)
```

## Module Descriptions

### 1. Retriever

**Goal:** Given a query, retrieve the most relevant passages from a corpus.

**Plan:**
- Start with **BM25** (lexical, bag-of-words scoring). Already prototyped with simple token overlap in `experiments/baseline_retrieval.py`.
- Upgrade to **dense retrieval** using a bi-encoder (e.g., Contriever or a sentence-transformer model) once the pipeline is wired together.
- Evaluate with Recall@k and MRR.

**Status:** Basic token-overlap prototype exists. BM25 via `rank_bm25` is next.

### 2. Generator

**Goal:** Given a query and top-k passages, generate a natural-language answer.

**Plan:**
- Use an open-source instruction-tuned LLM (candidates: Llama-3-8B, Mistral-7B).
- Prompt template: provide the passages as context, ask the model to answer based only on the context.
- Explore both zero-shot and few-shot prompting.

**Status:** Not implemented yet. We need to decide on model size vs. available compute.

### 3. Hallucination Analyzer

**Goal:** Given the query, retrieved passages, and generated answer, detect and categorize hallucinations.

**Hallucination Taxonomy:**

| Type | Definition | Detection Signal |
|------|-----------|-----------------|
| **Factual** | Claim contradicts established facts | Entity mismatch, factual inconsistency with external knowledge |
| **Contextual** | Claim not supported by retrieved passages | Low entailment score between answer sentence and any passage |
| **Reasoning** | Logical step in the answer is invalid | Broken inference chain, non-sequitur conclusions |
| **Faithfulness** | Answer distorts or exaggerates source meaning | Paraphrase divergence, sentiment/stance flip |

**Plan:**
- Phase 1 (current): Heuristic rules — token overlap, entity checking. See `experiments/hallucination_label_sketch.py`.
- Phase 2: Use an NLI model (e.g., DeBERTa fine-tuned on MNLI) for entailment-based detection.
- Phase 3: Train a lightweight classifier on top of NLI features + lexical features to predict the hallucination type.

**Status:** Heuristic sketch prototype exists. NLI integration is a near-term next step.

## Evaluation Plan

| What | Metric | Notes |
|------|--------|-------|
| Retrieval quality | Recall@5, Recall@10, MRR | Compare BM25 vs. dense |
| Answer quality | Token F1, ROUGE-L | Against gold answers |
| Hallucination detection | Precision, Recall, F1 | Binary: hallucinated or not |
| Hallucination typing | Macro F1 across 4 types | Requires typed annotations |

We may need to manually annotate a small evaluation set for hallucination typing, since existing datasets don't provide fine-grained hallucination labels.

## What Is NOT Implemented Yet

- Generator module (no LLM integrated)
- Dense retrieval
- NLI-based hallucination detection
- End-to-end pipeline connecting all modules
- Evaluation benchmarks
- Training of any models
- Web interface or API

This document will be updated as the project progresses.
