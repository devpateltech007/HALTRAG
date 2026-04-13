Here’s a more natural, “actually written by a dev” version — less robotic, a bit opinionated, and easier to read:

---

# HALT-RAG — Architecture & Design Notes

*Last updated: April 2026*

## Overview

This project is basically a RAG pipeline with an added twist — instead of just generating answers, we also try to **figure out when the model is hallucinating and why**.

The pipeline is split into three main parts:

1. Retrieve relevant context
2. Generate an answer
3. Analyze whether the answer is trustworthy

---

## High-Level Flow

```
User Query
    ↓
Retriever (BM25 → Dense later)
    ↓
Top-k Passages
    ↓
Generator (LLM)
    ↓
Answer
    ↓
Hallucination Analyzer
    ↓
(Type + Explanation)
```

---

## 1. Retriever

**What it does:**
Fetches the most relevant chunks of text for a given query.

**Current approach:**

* Started with a super basic token-overlap baseline (just to get things moving)
* Next step is plugging in **BM25** using `rank_bm25`

**Planned upgrades:**

* Move to **dense retrieval** (likely a bi-encoder setup)

  * Options: Contriever, sentence-transformers, etc.
* Compare lexical vs dense performance

**Metrics we care about:**

* Recall@k
* MRR

**Status:**
Baseline works. BM25 is the next quick win.

---

## 2. Generator

**What it does:**
Takes the retrieved passages + query and generates an answer.

**Plan:**

* Use an instruction-tuned open model (something like Llama or Mistral)
* Keep prompting simple:

  * Provide context
  * Ask the model to answer *strictly based on it*

**Things to experiment with:**

* Zero-shot vs few-shot prompts
* How strict we want to be about “don’t use outside knowledge”

**Open question:**

* Model size vs latency vs cost (still undecided)

**Status:**
Not built yet.

---

## 3. Hallucination Analyzer (core idea)

**What it does:**
Given:

* query
* retrieved passages
* generated answer

…it tries to detect:

* **Is this hallucinated?**
* **If yes, what kind?**

---

## Hallucination Types (working taxonomy)

We’re breaking hallucinations into 4 buckets:

### 1. Factual

* Straight-up wrong facts
* Example: wrong dates, wrong entities

**Signal:**

* Conflicts with known facts or entities

---

### 2. Contextual

* Not supported by retrieved passages

**Signal:**

* No strong entailment between answer and any passage

---

### 3. Reasoning

* The logic is broken even if facts look okay

**Signal:**

* Weird jumps in reasoning / non-sequitur conclusions

---

### 4. Faithfulness

* Twists or exaggerates what the source says

**Signal:**

* Meaning drift, tone flip, overgeneralization

---

## Detection Strategy

### Phase 1 (current)

* Heuristics:

  * token overlap
  * simple entity checks
* Basically just to validate the pipeline

---

### Phase 2

* Add **NLI model** (entailment-based)

  * Compare each answer sentence with passages
  * Check if it’s supported / contradicted

---

### Phase 3

* Train a lightweight classifier

  * Inputs:

    * NLI scores
    * lexical features
  * Output:

    * hallucination type

---

**Status:**
Only heuristic prototype exists right now.

---

## Evaluation Plan

We’ll evaluate each piece separately first:

### Retrieval

* Recall@5 / @10
* MRR

### Generation

* Token F1
* ROUGE-L

### Hallucination Detection

* Precision / Recall / F1 (binary)

### Hallucination Typing

* Macro F1 across 4 categories

---

## Dataset Problem

There’s no clean dataset for **typed hallucinations**, so:

* We’ll probably annotate a small dataset ourselves
* Keep it focused and high quality instead of large

---

## What’s Missing (a lot 😅)

* No generator wired up yet
* No dense retrieval
* No NLI integration
* No end-to-end pipeline
* No eval pipeline
* No trained models
* No UI / API

---

## Notes / Thoughts

* The hallucination analyzer is the real differentiator here
* Need to be careful not to over-engineer too early
* Getting a clean eval setup will matter more than model tweaks initially

---

If you want, I can also:

* make this README more GitHub-polished
* turn it into a pitch deck (for hackathons / demos)
* or help you design the actual folder structure + code skeleton next

Just tell me 👍
