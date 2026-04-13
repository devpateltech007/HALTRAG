# Dataset Research Notes

*Compiled by Dev and Kenil — April 2026*

We surveyed several QA datasets to find ones suitable for building and evaluating a RAG pipeline with hallucination analysis. Below are our notes.

---

## 1. PubMedQA

- **Source:** Biomedical research abstracts from PubMed
- **Task:** Yes/No/Maybe question answering
- **Size:** ~1,000 expert-annotated; ~212k artificially generated
- **Why it's useful:**
  - Directly in the medical domain, which is one of our target areas.
  - Each question comes with a context (abstract) and a long-form answer, which is good for testing retrieval + generation.
  - The yes/no/maybe format makes it easy to check if the model's answer contradicts the evidence.
- **Limitations:**
  - Questions are narrowly scoped (based on paper conclusions).
  - The artificially generated portion may be noisy.
  - Doesn't have multi-hop reasoning — less useful for testing reasoning-type hallucinations.
- **Our take:** Strong candidate for early experiments, especially for contextual and faithfulness hallucination types.

## 2. TriviaQA

- **Source:** Trivia enthusiast websites + Wikipedia/web evidence
- **Task:** Open-domain QA with evidence documents
- **Size:** ~95k question-answer pairs with ~650k evidence documents
- **Why it's useful:**
  - Large scale — good for training and testing retrieval components.
  - Evidence documents are provided, so we can test whether the model's answer is grounded in retrieved text.
  - Well-studied benchmark with many baselines to compare against.
- **Limitations:**
  - Not domain-specific (trivia, not medical/legal).
  - Some evidence documents are noisy or only tangentially related.
  - Answers are often short factoid strings — less useful for testing long-form generation.
- **Our take:** Good for retrieval baseline development and factual hallucination detection. Less relevant for our medical/legal focus.

## 3. HotpotQA

- **Source:** Wikipedia
- **Task:** Multi-hop question answering (requires reasoning over 2+ documents)
- **Size:** ~113k question-answer pairs
- **Why it's useful:**
  - Multi-hop structure is great for testing **reasoning-type** hallucinations.
  - Provides supporting facts annotation — we know which sentences are needed to answer the question.
  - Two settings: distractor (given 10 paragraphs, 2 are gold) and fullwiki (open retrieval).
- **Limitations:**
  - Wikipedia domain, not medical/legal.
  - Some questions have been found to be solvable with shortcuts (single-hop reasoning).
  - Supporting fact annotations are at the sentence level, not claim level.
- **Our take:** Best dataset for reasoning hallucination experiments. The distractor setting is useful for testing whether the model gets confused by irrelevant passages.

## 4. QASPER

- **Source:** NLP research papers (full text)
- **Task:** Question answering over long scientific documents
- **Size:** ~5,000 questions over 1,585 papers
- **Why it's useful:**
  - Tests long-document retrieval and comprehension.
  - Questions are written by readers of the paper (information-seeking, not synthetic).
  - Answer types include extractive, abstractive, yes/no, and unanswerable.
- **Limitations:**
  - Small dataset compared to others.
  - NLP domain — not directly medical or legal (though the format transfers).
  - Requires processing full paper PDFs.
- **Our take:** Interesting for faithfulness testing (does the model faithfully represent what the paper says?), but probably a secondary dataset for us.

---

## Summary Table

| Dataset | Domain | Size | Multi-hop | Hallucination Types Best Tested |
|---------|--------|------|-----------|-------------------------------|
| PubMedQA | Medical | ~1k expert | No | Contextual, Faithfulness |
| TriviaQA | Open | ~95k | No | Factual |
| HotpotQA | Wikipedia | ~113k | Yes | Reasoning, Contextual |
| QASPER | Scientific | ~5k | Partial | Faithfulness |

## Current Decision

For **early experimentation**, we're using a hand-crafted sample corpus (`data/sample_corpus.json`) with medical and legal examples. This lets us iterate quickly without dealing with large dataset downloads and preprocessing.

For the **next phase**, we plan to start with **PubMedQA** (closest to our medical domain) and **HotpotQA** (best for reasoning hallucinations). TriviaQA and QASPER are lower priority for now but may be added later for broader evaluation.

## Download Links (for later)

- PubMedQA: https://pubmedqa.github.io/
- TriviaQA: https://nlp.cs.washington.edu/triviaqa/
- HotpotQA: https://hotpotqa.github.io/
- QASPER: https://allenai.org/data/qasper
