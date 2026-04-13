# Initial Experiments — Lab Notes

*Dev Patel & Kenil Vaghasiya — April 2026*

---

## Experiment 1: Token Overlap Retrieval on Sample Corpus

**Date:** April 8, 2026

**Goal:** Verify that a simple lexical retriever can rank documents sensibly on our sample data. This is a sanity check before moving to BM25 or dense retrieval.

**Setup:**
- Loaded the 8-document sample corpus (4 medical, 4 legal).
- Implemented token overlap scoring: for each query, tokenize both the query and each document, then compute the fraction of unique query tokens that appear in the document.
- Removed stopwords to reduce noise.

**Queries tested:**
1. "What is metformin used for?"
2. "What are the elements of medical malpractice?"
3. "How does warfarin interact with other drugs?"

**Observations:**
- The retriever correctly ranked the most relevant document first for all three queries.
- Query 1 returned `med_001` (Metformin) at the top. Query 2 returned `legal_002` (Malpractice). Query 3 returned `med_003` (Warfarin).
- Scores were low overall (0.3–0.5 range) because the query tokens are short and many content words don't exactly match.
- The ranking for lower-ranked results was less meaningful — most documents scored close to 0.

**Issues:**
- Token overlap doesn't handle synonyms. "medication" in the document vs. "drug" in the query = no match.
- No term weighting — rare terms and common terms contribute equally.
- This clearly won't work on a real dataset. We need BM25 at minimum.

**Next:** Integrate `rank_bm25` library and re-run on the same queries to compare.

---

## Experiment 2: Heuristic Hallucination Labeling

**Date:** April 10, 2026

**Goal:** Test whether simple rules can distinguish between hallucination categories on hand-crafted examples. The point is to explore what signals are available, not to build a real detector.

**Setup:**
- Wrote 5 examples: one grounded answer and one for each hallucination type (factual, contextual, reasoning, faithfulness).
- Heuristics:
  - **Factual:** Detect entities in the answer that don't appear in the context (naive capitalized-word extraction).
  - **Contextual:** Low token coverage — most answer tokens aren't in the context.
  - **Reasoning:** Negation mismatch between context and answer.
  - **Faithfulness:** High density of absolutist/exaggeration words.

**Observations:**
- The grounded example was correctly classified — high coverage, no red flags.
- The factual example was caught because "Amoxicillin" appeared in the answer but not the context.
- The contextual example was caught because the answer introduced many tokens not in the context (cybersecurity, genetic data, etc.).
- The reasoning example was partially caught via negation mismatch ("does not" vs. "causes").
- The faithfulness example was caught due to "absolutely", "guaranteed", "always", "every", "definitely".

**Issues:**
- Entity extraction is very crude. It misses entities that aren't capitalized and produces false positives on common capitalized words.
- Token coverage is a blunt instrument. A long answer with many novel *but correct* elaborations would be flagged as contextual hallucination.
- Negation detection is fragile. "Metformin is not dangerous" vs. "Metformin is safe" — no negation word in the second one, so the heuristic misses the equivalence.
- The boundaries between categories are blurry. Some examples could be labeled as multiple types.
- These heuristics would fall apart on real data. We need NLI for contextual/faithfulness and probably entity linking for factual.

**Takeaways:**
- The hallucination taxonomy (4 types) seems workable, but operationalizing the boundary between "contextual" and "faithfulness" needs more thought.
- Token-level features are useful as *part* of a feature set, but insufficient alone.
- We should look into using a pre-trained NLI model (DeBERTa-v3-large on MNLI) as the backbone for detection.

**Next:**
- Try using `sentence-transformers` to compute semantic similarity instead of token overlap.
- Look into the `transformers` library for loading an NLI model.
- Design a small set of ~20 hand-labeled examples that cover edge cases to use as a mini evaluation set.

---

## Experiment 3 (planned): BM25 Retrieval

**Date:** TBD

**Goal:** Replace token overlap with proper BM25 using `rank_bm25` and compare retrieval quality.

**Plan:**
- Use the same sample corpus and queries.
- Compare ranked lists and scores with Experiment 1.
- If results look good, try on a small slice of PubMedQA.

---

## Experiment 4 (planned): NLI-Based Entailment for Hallucination Detection

**Date:** TBD

**Goal:** Use a pre-trained NLI model to score whether each answer sentence is entailed by the context.

**Plan:**
- Load `cross-encoder/nli-deberta-v3-base` from HuggingFace.
- For each (context, answer_sentence) pair, get entailment/neutral/contradiction probabilities.
- Use contradiction as a signal for hallucination.
- See if entailment scores correlate with our heuristic labels.
