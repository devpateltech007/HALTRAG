# HALT-RAG · System Architecture

HALT-RAG is a Trust-Aware Retrieval-Augmented Generation pipeline. It does not
treat the LLM as an oracle and it does not treat the hallucination detector as
an oracle either. Every layer is independent and every claim is auditable.

## High-level diagram

```
                ┌─────────────────────────────┐
                │           Question          │
                └──────────────┬──────────────┘
                               │
                               ▼
                ┌─────────────────────────────┐
                │  Dense retriever (MiniLM    │
                │  embeddings + FAISS index)  │
                └──────────────┬──────────────┘
                               │ top-K contexts
                               ▼
                ┌─────────────────────────────┐
                │  Generator (Gemini, with    │
                │  extractive fallback)       │
                └──────────────┬──────────────┘
                               │ answer
                               ▼
        ┌──────────────────────────────────────────┐
        │  Deep Hallucination Detector             │
        │  - sentence segmentation                 │
        │  - NLI entailment vs context             │
        │  - semantic similarity                   │
        │  - lexical overlap                       │
        │  - retrieval strength                    │
        │  → grounded / uncertain / hallucinated   │
        └──────────────┬───────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │  Hallucination classifier                │
        │  type ∈ {faithful, factual,              │
        │          contextual, reasoning}          │
        └──────────────┬───────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │  Detector validation                     │
        │  multi-signal confidence + agreement     │
        └──────────────┬───────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │  Confidence scoring + risk bucketing     │
        └──────────────┬───────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │  API response → Next.js UI               │
        │  Append-only JSONL audit log             │
        └──────────────────────────────────────────┘
```

## Components

### Retrieval — `src/retrieval.py`
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` with a deterministic
  local fallback when weights are unavailable.
- Index: FAISS L2/inner-product index persisted under `data/corpus/`.
- Dynamic corpus is appended to `data/dynamic_knowledge.jsonl` and reloaded on
  each admin update.

### Generation — `src/generation.py`
- Gemini provider when `GEMINI_API_KEY` is configured (`GENERATION_PROVIDER`).
- Deterministic extractive fallback that stitches together top retrieved
  sentences. Always returns an answer + provider tag.

### Sentence-level verifier — `src/deep_hallucination_detector.py`
- Splits the answer into sentences.
- For each sentence, computes:
  - NLI entailment / contradiction (via `src/models/nli_model.py`)
  - Semantic similarity (via `src/models/embedding_model.py`)
  - Lexical overlap with retrieved context
  - Retrieval strength (max retrieval score among supporting contexts)
- Labels each sentence `grounded`, `uncertain`, or `hallucinated`.

### Hallucination classifier — `src/hallucination_classifier.py`
- Aggregates sentence-level labels into one of:
  - `faithful` — strongly supported by retrieved sources
  - `factual` — possible factual hallucination
  - `contextual` — mismatch with retrieved evidence
  - `reasoning` — unsupported inferential step

### Detector validator — `src/detector_validation.py`
- Returns `detector_confidence`, `agreement_level` (low/medium/high), and a
  `signal_disagreement` flag — used to lower trust when signals fight each other.

### Confidence scoring — `src/confidence.py`
- Composes retrieval quality + sentence grounding + detector validation +
  signal agreement into a single 0–1 trust score and a risk bucket.

### Knowledge updates — `src/knowledge_update.py`
- Chunk + embed + persist (FAISS / vector store).
- Reload retriever — no LLM retraining required.

### Audit logging — `src/audit.py`
- Append-only JSONL trace at `logs/audit.jsonl`:
  question, answer, confidence, risk, hallucination type, detector signals,
  retrieved source IDs, provider, latency.

## API surface — `backend/main.py`

| Method | Path                    | Description                                |
| ------ | ----------------------- | ------------------------------------------ |
| GET    | `/health`               | Liveness probe                             |
| POST   | `/query`                | Run full retrieve → generate → verify trace|
| POST   | `/admin/add_document`   | Insert verified document into vector store |
| POST   | `/admin/add_qa`         | Insert verified Q&A into vector store      |
| GET    | `/logs`                 | Read audit log (filter by risk / type)     |

## Frontend — `frontend/`

Next.js 14 app, dark glassmorphism theme, Tailwind CSS. Pages:

- `/` — Dashboard (status pills, pipeline overview, recent activity).
- `/ask` — Query console (answer, confidence, risk, type, detector panel,
  sentence-level grounding, source evidence).
- `/admin` — Knowledge update (document or Q&A).
- `/logs` — Audit log table with filters by risk / type / provider.
- `/about` — Methodology and the "is the detector hallucinating?" answer.

## Design principles

1. **Separation of concerns** — generator and verifier never share weights.
2. **Probabilistic** — trust is a graded signal, not a yes/no verdict.
3. **Transparent** — every signal, every score, every source is exposed.
4. **Auditable** — every query is JSONL-logged with full trace.
5. **Dynamic** — knowledge updates without retraining.
