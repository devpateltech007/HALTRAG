from __future__ import annotations
import logging
import os
import re
from typing import Any

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(*_: object, **__: object) -> bool:
        return False

logger = logging.getLogger(__name__)


MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
UNKNOWN_ANSWER = "I don't know based on the provided sources."


def generate_answer(question: str, retrieved_contexts: list[dict[str, Any]]) -> str:
    """Return an answer string, using Gemini when configured and fallback otherwise."""
    return generate_with_provider(question, retrieved_contexts)["answer"]


def generate_with_provider(question: str, retrieved_contexts: list[dict[str, Any]]) -> dict[str, str]:
    load_dotenv()
    context = _format_context(retrieved_contexts)
    if not context.strip():
        logger.info("Generation fell back to extractive output because no retrieved context was available.")
        return {"answer": UNKNOWN_ANSWER, "provider": "extractive"}

    if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) and os.getenv("GENERATION_PROVIDER", "gemini").lower() == "gemini":
        answer = _gemini_answer(question, context)
        if answer:
            logger.info("Gemini generation succeeded with model %s.", MODEL_NAME)
            return {"answer": answer, "provider": "gemini"}

        logger.warning("Gemini generation returned no answer; using extractive fallback.")

    return {"answer": extractive_fallback(question, retrieved_contexts), "provider": "extractive"}


def extractive_fallback(question: str, retrieved_contexts: list[dict[str, Any]]) -> str:
    """Select a grounded sentence from retrieved contexts."""
    sentences: list[str] = []
    for context in retrieved_contexts or []:
        sentences.extend(_split_sentences(context.get("text", "")))
    if not sentences:
        return UNKNOWN_ANSWER

    question_tokens = set(_tokens(question))
    best_sentence = max(
        sentences,
        key=lambda sentence: len(set(_tokens(sentence)) & question_tokens) / max(1, len(question_tokens)),
    )
    if not best_sentence.strip():
        return UNKNOWN_ANSWER
    return best_sentence.strip()


def _gemini_answer(question: str, context: str) -> str | None:
    prompt = (
        "Answer ONLY using the provided context. "
        "If the answer is unsupported, say exactly: "
        f"{UNKNOWN_ANSWER}\n\n"
        f"Context:\n{context[:12000]}\n\nQuestion: {question}\n\nAnswer:"
    )

    try:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set; Gemini is unavailable.")
            return None

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        text = getattr(response, "text", None)
        if text and text.strip():
            logger.info("Gemini response received from model %s (%d chars).", MODEL_NAME, len(text.strip()))
            return text.strip()

        logger.warning("Gemini response was empty for model %s.", MODEL_NAME)
        return None
    except Exception as exc:
        logger.exception("Gemini generation failed for model %s: %s", MODEL_NAME, exc)
        return None


def _format_context(retrieved_contexts: list[dict[str, Any]]) -> str:
    blocks = []
    for idx, source in enumerate(retrieved_contexts or [], start=1):
        source_id = source.get("source_id") or source.get("id") or f"source_{idx}"
        blocks.append(f"[{source_id}]\n{source.get('text', '')}")
    return "\n\n".join(blocks)


def _split_sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text or "") if len(part.strip()) > 2]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?", (text or "").lower())
