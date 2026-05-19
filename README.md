# HALT-RAG · Trust-Aware Retrieval-Augmented Generation

> Detect, classify, and localize hallucinations in high-stakes AI answers.

HALT-RAG is a **graduate-research-grade** retrieval-augmented generation
system designed for high-stakes domains (medical / legal QA). It separates
**generation** from **verification** and treats the hallucination detector
as a **probabilistic trust signal** rather than an oracle. Every answer is
graded, every sentence is localized, every signal is exposed, every query
is audit-logged.

This `HALT-RAG-FINAL/` directory is the **clean final runnable system**.
The repository root above it preserves legacy experiments, notebooks,
prototypes, proposal PDFs, and prior coursework.

---

## 1. Project overview

| Layer            | Component                                     | File                                  |
| ---------------- | --------------------------------------------- | ------------------------------------- |
| API              | FastAPI app                                    | `backend/main.py`                     |
| Retrieval        | MiniLM embeddings + FAISS                      | `src/retrieval.py`                    |
| Generation       | Gemini + extractive fallback                   | `src/generation.py`                   |
| Sentence verifier| NLI + similarity + overlap + retrieval         | `src/deep_hallucination_detector.py`  |
| Answer classifier| `faithful / factual / contextual / reasoning`  | `src/hallucination_classifier.py`     |
| Detector validator| multi-signal confidence + agreement           | `src/detector_validation.py`          |
| Confidence       | composite trust score                          | `src/confidence.py`                   |
| Knowledge update | dynamic chunk + embed + reload                 | `src/knowledge_update.py`             |
| Audit            | append-only JSONL                              | `src/audit.py`                        |
| Frontend         | Next.js 14 + Tailwind dark dashboard           | `frontend/`                           |

---

## 2. System architecture

```
Question
  → Dense retriever (MiniLM + FAISS)
  → Generator (Gemini / extractive fallback)
  → Sentence-level grounding (NLI · similarity · overlap · retrieval)
  → Hallucination classifier (faithful / factual / contextual / reasoning)
  → Detector validation (multi-signal agreement)
  → Confidence + risk
  → API/UI + JSONL audit log
```

Full diagram in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## 3. Deep-learning components

- **`sentence-transformers/all-MiniLM-L6-v2`** for retrieval and semantic
  similarity (with deterministic local fallback).
- **Hugging Face NLI model** (cross-encoder) for entailment / contradiction.
- **FAISS** for dense nearest-neighbour search.
- **Gemini** for answer generation when `GEMINI_API_KEY` is configured.

All components have local fallbacks so the demo is reproducible without
external API keys.

---

## 4. Dataset strategy

- Curated demo corpus under `data/corpus/` (FAISS + JSONL metadata).
- Curated **evaluation set** at `data/eval/halt_rag_eval.csv` — 40 cases
  covering all four hallucination types in medical / legal QA.
- Dynamic admin updates are appended to `data/dynamic_knowledge.jsonl` and
  reloaded into the retriever.

---

## 5. Dynamic knowledge updates

The admin page (`/admin` in the UI) allows verified documents and Q&A
pairs to be added at runtime:

1. Text is chunked.
2. Chunks are embedded with the same MiniLM encoder.
3. The new vectors are persisted to the vector store.
4. The retriever is reloaded — **the LLM is never retrained**.

This demonstrates how a RAG system can absorb new evidence without the
cost or risk of fine-tuning.

---

## 6. Hallucination detection methodology

For every answer sentence the detector computes:

- **NLI entailment** vs. the best retrieved context.
- **Semantic similarity** in embedding space.
- **Lexical overlap** of content tokens.
- **Retrieval strength** of the supporting context.

These signals are combined into a sentence-level label:

- 🟢 `grounded` · 🟠 `uncertain` · 🔴 `hallucinated`

And aggregated into an answer-level type:

- `faithful` · `factual` · `contextual` · `reasoning`

---

## 7. Why the detector is probabilistic

We deliberately avoid claiming hallucination elimination. The detector is
a **probabilistic trust signal**, not a verdict. Its independence and
multi-signal design make it more robust than a single classifier, but it
is still fallible — and so we expose its uncertainty rather than hide it.

Full discussion in [`docs/PROFESSOR_QA.md`](docs/PROFESSOR_QA.md).

---

## 8. Evaluation metrics

Detector evaluation:

```bash
python -m src.evaluate_detector
```

Generates:

- `results/evaluation_report.json` — accuracy, macro F1, per-case detector signals.
- `results/confusion_matrix.png`
- `results/type_distribution.png`
- `results/confidence_distribution.png`

Full evaluation methodology in [`docs/EVALUATION.md`](docs/EVALUATION.md).

---

## 9. Ablation study

```bash
python -m src.ablation
```

Generates `results/ablation_results.csv` — detector accuracy with each
signal removed one at a time. This is the empirical answer to "why four
signals?" — every signal contributes; removing any of them measurably
degrades performance.

---

## 10. Run instructions

### 10.1 Install (Python backend)

```bash
pip install -r requirements.txt
```

Optional environment variables (see `.env.example`):

```
GEMINI_API_KEY=
GENERATION_PROVIDER=gemini
```

If the key is missing, generation falls back to an extractive answer
built from the top retrieved sentences.

### 10.2 Run the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

Endpoints: `/health`, `/query`, `/admin/add_document`, `/admin/add_qa`,
`/logs`.

### 10.3 Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://127.0.0.1:3000> — the trust-aware dashboard.

### 10.4 Run the tests

```bash
pytest
```

---

## 11. Project structure

```text
HALT-RAG-FINAL/
├── backend/                FastAPI app
│   ├── __init__.py
│   ├── api.py              compatibility wrapper
│   └── main.py             create_app + endpoints
├── src/
│   ├── ablation.py
│   ├── audit.py
│   ├── confidence.py
│   ├── config.py
│   ├── deep_hallucination_detector.py
│   ├── detector_validation.py
│   ├── evaluate_detector.py
│   ├── generation.py
│   ├── hallucination_classifier.py
│   ├── knowledge_update.py
│   ├── retrieval.py
│   ├── utils.py
│   └── models/
│       ├── embedding_model.py
│       └── nli_model.py
├── frontend/               Next.js 14 + Tailwind dark dashboard
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── globals.css
│   │   ├── page.tsx               Dashboard
│   │   ├── ask/page.tsx           Ask console
│   │   ├── admin/page.tsx         Knowledge update
│   │   ├── logs/page.tsx          Audit log table
│   │   └── about/page.tsx         Methodology
│   ├── components/                Reusable UI
│   ├── lib/api.ts                 typed API client
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── tsconfig.json
│   └── package.json
├── data/
│   ├── corpus/             FAISS index + metadata
│   ├── eval/               curated evaluation set
│   └── sample_corpus.json  fallback corpus
├── docs/                   architecture · evaluation · QA · limitations
├── logs/                   audit.jsonl
├── results/                evaluation + ablation artifacts
├── tests/                  pytest suite
├── requirements.txt
├── .env.example
└── FINAL_PROJECT_STRUCTURE.md
```

---

## 12. Limitations

See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md). In summary:

- The demo corpus is small and curated.
- The detector is **probabilistic**, not exact — high-risk answers should
  still receive human review.
- The system does **not** claim to eliminate hallucinations.
- It is an **academic demonstration**, not a clinical / legal tool.

---

## 13. Future work

- Scale the corpus to a domain-specific production knowledge base.
- Replace the local NLI model with a higher-capacity entailment model.
- Add active-learning loops for detector calibration on user feedback.
- Add per-user roles + authentication on the admin endpoints.
- Add streaming responses and incremental sentence verification.
- Add cross-model verification (use a second LLM as an independent judge).

---

## API quick reference

### `POST /query`

```json
{ "question": "What does HIPAA protect?", "top_k": 5 }
```

Response includes: `answer`, `confidence`, `risk`, `hallucination_type`,
`provider`, `retrieved_sources`, `sentence_analysis`, `detector_signals`.

### `POST /admin/add_document`

```json
{ "text": "…", "uploader": "admin", "domain": "medical", "verified": true }
```

### `POST /admin/add_qa`

```json
{ "question": "…", "answer": "…", "uploader": "admin", "verified": true }
```

### `GET /logs?limit=50&risk=high&hallucination_type=factual`

Returns the recent audit trail filtered by risk / type.

### `GET /health`

Returns `{ "status": "ok", "service": "halt-rag" }`.

---

### Language we deliberately avoid

- "Hallucination eliminated."
- "Guaranteed factual."
- "Verified by AI."

### Language we use

- **Trust-aware.**
- **Probabilistic.**
- **Interpretable.**
- **Auditable.**
