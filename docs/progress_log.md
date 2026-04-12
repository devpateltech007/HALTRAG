# Progress Log

---

### Week 1 — March 24–30, 2026

**Brainstorming & Topic Selection**

- Met to discuss potential project ideas. We both wanted to work on something related to LLMs and reliability.
- Dev suggested focusing on hallucination detection since it's a hot topic and practically important.
- Kenil proposed combining it with RAG since pure hallucination detection without context is harder to scope.
- We agreed on the idea: build a RAG system that not only detects hallucinations but **classifies them by type**.
- Decided to target medical and legal QA as the application domain because hallucinations are most dangerous there.

**Literature Review**

- Read the original RAG paper (Lewis et al., 2020) to understand the retrieval-augmented generation setup.
- Looked at the hallucination survey by Ji et al. (2023) — very comprehensive, helped us define our taxonomy.
- Skimmed SelfCheckGPT and FActScore papers for ideas on detection methods.
- Kenil found a few recent papers on hallucination in medical QA specifically — will add citations later.

---

### Week 2 — March 31 – April 6, 2026

**Dataset Exploration**

- Dev explored PubMedQA and TriviaQA — downloaded samples, looked at the data format.
- Kenil explored HotpotQA and QASPER — checked sizes, availability, and how questions are structured.
- We compared all four datasets in a meeting and wrote up notes (see `dataset_notes.md`).
- Decided PubMedQA and HotpotQA are our primary candidates.

**Architecture Discussion**

- Whiteboarded the pipeline: retriever → generator → analyzer.
- Discussed what "hallucination typing" means concretely — came up with four categories (factual, contextual, reasoning, faithfulness).
- Talked about how to detect each type: entity matching for factual, NLI for contextual, chain-of-thought analysis for reasoning.
- Kenil drafted the architecture doc.

**Early Setup**

- Created the GitHub repo and set up the project structure.
- Dev wrote the `.gitignore` and `requirements.txt`.
- Created a small sample corpus with medical and legal examples for local testing.

---

### Week 3 — April 7–13, 2026

**First Code**

- Dev implemented `baseline_retrieval.py` — a simple token overlap retriever that loads the sample corpus and ranks documents for a query. Nothing fancy, but it runs and gives sensible results on our small data.
- Kenil wrote `hallucination_label_sketch.py` — a heuristic-based prototype that takes an answer and context and tries to classify the hallucination type using simple rules (token overlap, negation detection, entity checking). It's rough but helps us think about what features matter.

**Testing & Discussion**

- Ran both scripts on sample data and discussed the output.
- The retriever works fine for toy examples but obviously won't scale — need BM25 at minimum.
- The heuristic labeler is very brittle. It catches obvious cases (e.g., entity mismatch → factual) but misses subtle ones. We need NLI or a learned model.
- Discussed next steps: integrate `rank_bm25`, download PubMedQA, start thinking about the generator module.

**Documentation**

- Wrote initial experiment notes in `notebooks/initial_experiments.md`.
- Updated this progress log.
- Created team work split document.

---

### Next: Week 4 — April 14–20, 2026 (planned)

- [ ] Integrate `rank_bm25` for proper BM25 retrieval
- [ ] Download and preprocess PubMedQA
- [ ] Explore using a small LLM for the generator (Llama-3-8B or Mistral-7B)
- [ ] Start replacing heuristics with NLI-based entailment checking
- [ ] Design a small annotation scheme for hallucination typing evaluation
