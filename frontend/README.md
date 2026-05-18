# HALT-RAG Frontend

Presentation-grade Next.js + shadcn UI for the VeritasRAG project.

## What it includes

- Query console for medical QA prompts
- Visual pipeline stages (Retriever, Generator, Analyzer)
- Tabs for generated answer, retrieved evidence, and hallucination typing
- API route at `src/app/api/pipeline/route.ts`:
  - Tries to execute the real Python pipeline (`python -m src.pipeline`)
  - Falls back to demo response if Python environment is unavailable

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Demo tips for presentation

- Use quick query chips to speed up live demo.
- Mention `Source: Live Python pipeline` when Python integration succeeds.
- If environment issues happen, app still works via `Source: Demo fallback`.
