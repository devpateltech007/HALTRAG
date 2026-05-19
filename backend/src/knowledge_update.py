from __future__ import annotations
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from src.models.embedding_model import encode_texts
from src.retrieval import (
    CORPUS_DIR,
    DYNAMIC_KNOWLEDGE_PATH,
    load_corpus_documents,
    rebuild_index,
)


DEFAULT_CHUNK_TOKENS = 120
DEFAULT_CHUNK_OVERLAP = 30
logger = logging.getLogger(__name__)


class KnowledgeUpdater:
    """Persist document and verified Q&A updates, then rebuild dense retrieval."""

    def __init__(
        self,
        dynamic_path: str | Path = DYNAMIC_KNOWLEDGE_PATH,
        vector_store_dir: str | Path = CORPUS_DIR,
    ):
        self.dynamic_path = Path(dynamic_path)
        self.vector_store_dir = Path(vector_store_dir)

    def add_document(
        self,
        text: str,
        uploader: str | None = None,
        domain: str | None = None,
        verified: bool = False,
        title: str | None = None,
        source_id: str | None = None,
    ) -> dict[str, Any]:
        return self._add_records(
            text=text,
            uploader=uploader,
            domain=domain or "general",
            verified=verified,
            source_type="document",
            title=title or "Admin document update",
            source_id=source_id,
        )

    def add_qa(
        self,
        question: str,
        answer: str,
        uploader: str | None = None,
        domain: str | None = None,
        verified: bool = True,
        source_id: str | None = None,
    ) -> dict[str, Any]:
        clean_question = (question or "").strip()
        clean_answer = (answer or "").strip()
        if not clean_question or not clean_answer:
            raise ValueError("Question and answer are required for a Q&A update.")
        text = f"Question: {clean_question}\nVerified answer: {clean_answer}"
        return self._add_records(
            text=text,
            uploader=uploader,
            domain=domain or "general",
            verified=verified,
            source_type="qa_pair",
            title=clean_question[:120],
            source_id=source_id,
        )

    def _add_records(
        self,
        text: str,
        uploader: str | None,
        domain: str,
        verified: bool,
        source_type: str,
        title: str,
        source_id: str | None,
    ) -> dict[str, Any]:
        clean_text = (text or "").strip()
        if not clean_text:
            logger.warning("Rejected empty %s knowledge update.", source_type)
            raise ValueError("Knowledge update text cannot be empty.")

        chunks = chunk_text(clean_text)
        if not chunks:
            logger.warning("Rejected %s knowledge update with no usable chunks.", source_type)
            raise ValueError("Knowledge update text did not contain usable content.")

        timestamp = datetime.now(timezone.utc).isoformat()
        source_id = source_id or f"{source_type}_{uuid.uuid4().hex[:10]}"
        records = []
        embeddings = encode_texts(chunks)
        logger.info(
            "Adding %s knowledge source %s with %d chunks. verified=%s domain=%s uploader=%s.",
            source_type,
            source_id,
            len(chunks),
            bool(verified),
            domain or "general",
            uploader or "admin",
        )

        for idx, chunk in enumerate(chunks, start=1):
            record_id = f"{source_id}_chunk_{idx:03d}"
            metadata = {
                "source_id": source_id,
                "record_id": record_id,
                "timestamp": timestamp,
                "verified": bool(verified),
                "source_type": source_type,
                "uploader": uploader or "admin",
                "domain": domain or "general",
                "title": title,
                "chunk_index": idx,
                "chunk_count": len(chunks),
            }
            records.append(
                {
                    "source_id": record_id,
                    "id": record_id,
                    "text": chunk,
                    "verified": bool(verified),
                    "metadata": metadata,
                    "embedding_norm": float((embeddings[idx - 1] ** 2).sum() ** 0.5),
                }
            )

        self._append_jsonl(records)
        if self.dynamic_path == DYNAMIC_KNOWLEDGE_PATH and self.vector_store_dir == CORPUS_DIR:
            vector_summary = rebuild_index(load_corpus_documents())
        else:
            vector_summary = self._persist_local_vector_store()
        logger.info(
            "Knowledge source %s persisted. chunks=%d vector_documents=%s metadata_path=%s.",
            source_id,
            len(records),
            vector_summary.get("documents"),
            vector_summary.get("metadata_path"),
        )
        return {
            "source_id": source_id,
            "chunks_added": len(records),
            "verified": bool(verified),
            "source_type": source_type,
            "vector_store": vector_summary,
        }

    def _append_jsonl(self, records: list[dict[str, Any]]) -> None:
        self.dynamic_path.parent.mkdir(parents=True, exist_ok=True)
        with self.dynamic_path.open("a", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        logger.info("Appended %d knowledge records to %s.", len(records), self.dynamic_path)

    def _persist_local_vector_store(self) -> dict[str, Any]:
        records = load_dynamic_documents(self.dynamic_path)
        texts = [record.get("text", "") for record in records]
        embeddings = encode_texts(texts)
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        embeddings_path = self.vector_store_dir / "hash_embeddings.npy"
        metadata_path = self.vector_store_dir / "metadata.jsonl"

        import numpy as np

        np.save(embeddings_path, embeddings)
        with metadata_path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        logger.info(
            "Persisted local vector store at %s with %d records and embedding_dim=%d.",
            self.vector_store_dir,
            len(records),
            int(embeddings.shape[1]) if len(embeddings) else 384,
        )

        return {
            "documents": len(records),
            "embedding_dim": int(embeddings.shape[1]) if len(embeddings) else 384,
            "embeddings_path": str(embeddings_path),
            "metadata_path": str(metadata_path),
            "faiss_path": None,
        }


def add_document(
    text: str,
    uploader: str | None = None,
    domain: str | None = None,
    verified: bool = False,
) -> dict[str, Any]:
    return KnowledgeUpdater().add_document(
        text=text,
        uploader=uploader,
        domain=domain,
        verified=verified,
    )


def add_qa(
    question: str,
    answer: str,
    uploader: str | None = None,
    domain: str | None = None,
    verified: bool = True,
) -> dict[str, Any]:
    return KnowledgeUpdater().add_qa(
        question=question,
        answer=answer,
        uploader=uploader,
        domain=domain,
        verified=verified,
    )


def chunk_text(
    text: str,
    max_tokens: int = DEFAULT_CHUNK_TOKENS,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    tokens = re.findall(r"\S+", text or "")
    if not tokens:
        return []
    if len(tokens) <= max_tokens:
        return [text.strip()]

    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunks.append(" ".join(tokens[start:end]).strip())
        if end == len(tokens):
            break
        start = max(0, end - overlap)
    return chunks


def load_dynamic_documents(path: str | Path = DYNAMIC_KNOWLEDGE_PATH) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def load_augmented_corpus() -> list[dict[str, Any]]:
    """Compatibility helper for legacy modules."""
    return load_corpus_documents()
