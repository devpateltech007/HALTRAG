# HALT-RAG Limitations

HALT-RAG is a research demo for trust aware RAG. It is not a real medical or legal advisor.

This section explains the current limitations of the system so the committee, users, and future developers can understand what the project can and cannot do.

## 1. The Corpus Is Small and Curated

The demo corpus is stored in:

```bash
data/corpus/
```

This corpus is intentionally small so the project is easy to run and reproduce without downloading a huge dataset.

Because of this, the retriever can only find information that already exists in the corpus. The verifier can also only check answers against the context that was retrieved.

For a real production system, we would need a much bigger knowledge base and a stronger ingestion pipeline.

## 2. The Detector Is Probabilistic

The hallucination detector does not give a perfect yes or no answer.

Instead, it gives a trust signal based on several scores:

- NLI entailment
- semantic similarity
- lexical overlap
- retrieval strength

Each signal has weaknesses.

NLI models can struggle with multi-step reasoning, negation, and numbers.

Semantic similarity can be affected by how well something is paraphrased.

Lexical overlap can be fooled when two sentences use similar words but mean different things.

Retrieval strength only depends on the top retrieved documents, so it can miss useful evidence that was not retrieved.

This is why HALT-RAG combines multiple signals instead of trusting only one.

## 3. The Detector Is Not an Oracle

The detector can still be wrong.

If all four signals fail in the same direction, the system might produce a confident trust score that is still incorrect.

This is rare, but it can happen.

That is why HALT-RAG logs every answer, exposes the signal scores, and marks risky answers for human review.

High-risk outputs should always be checked by a person.

## 4. The Generator Depends on External Services

The LLM generation uses Gemini, which requires:

```bash
GEMINI_API_KEY
```

If the API key is missing, invalid, or the service is unavailable, the system uses an extractive fallback generator.

The fallback generator builds an answer by stitching together retrieved sentences.

This fallback is safer because it sticks closely to the retrieved text, but it is usually less fluent than an LLM-generated answer.

## 5. Sentence Splitting Is Basic

HALT-RAG splits answers into sentences using a regex-based sentence splitter.

This works for many normal answers, but it can make mistakes with:

- unusual punctuation
- bullet points
- numbered lists
- long structured answers

To reduce this issue, the system also computes answer-level signals in addition to sentence-level signals.

## 6. Latency

End-to-end latency includes:

- retrieval
- answer generation
- NLI verification
- similarity scoring
- logging

On normal hardware without a GPU, the verifier is usually the slowest part.

The fallback paths are faster, but they may reduce answer quality or fluency.

## 7. Evaluation Scale

The evaluation set has 40 curated cases.

This is enough to demonstrate the main idea of the detector, but it is not the same as testing on a large benchmark.

Larger benchmarks include:

- TruthfulQA
- HaluEval
- RAGTruth

The 40 cases were chosen to cover different hallucination types and both medical and legal demo topics.

## 8. Not a Clinical or Legal Tool

HALT-RAG should not be used for real medical or legal advice.

It is only an academic demonstration of how a RAG system can be made more transparent, auditable, and trust-aware.

## 9. Bias and Dataset Coverage

The system depends on the documents that are added to the corpus.

Because the demo corpus focuses on medical and legal examples, the outputs may be biased toward those topics and the language used in those documents.

If new documents are added, the system also inherits the strengths and weaknesses of those documents.

## What HALT-RAG Does Not Claim

HALT-RAG does not claim to eliminate hallucinations.

It does not claim to know with certainty whether every answer is correct.

It does not replace human review for important medical, legal, or high-stakes decisions.

## What HALT-RAG Does Provide

HALT-RAG provides a probabilistic trust layer on top of an LLM-based RAG system.

That trust layer is:

- interpretable
- auditable
- based on multiple signals
- useful for flagging risky answers

The main point is that the trust score is a signal, not a final verdict.
