from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import numpy as np
from src.models.embedding_model import EMBEDDING_DIM, encode_query, encode_texts

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CORPUS_DIR = DATA_DIR / "corpus"
SAMPLE_CORPUS_PATH = DATA_DIR / "sample_corpus.json"
DYNAMIC_KNOWLEDGE_PATH = CORPUS_DIR / "dynamic_knowledge.jsonl"
LEGACY_DYNAMIC_KNOWLEDGE_PATH = DATA_DIR / "dynamic_knowledge.jsonl"
INDEX_PATH = CORPUS_DIR / "halt_rag.faiss"
EMBEDDINGS_PATH = CORPUS_DIR / "embeddings.npy"
METADATA_PATH = CORPUS_DIR / "metadata.jsonl"


class DenseRetriever:
    """Dense retriever using normalized embeddings and FAISS when available."""

    def __init__(self, corpus: list[dict[str, Any]] | None = None, force_rebuild: bool = False):
        self.corpus = corpus or load_corpus_documents()
        if not self.corpus:
            self.corpus = []
        self._faiss = _import_faiss()
        self.embeddings: np.ndarray
        self.index = None
        self._load_or_build(force_rebuild=force_rebuild)

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not query or not self.corpus:
            return []

        top_k = max(1, min(int(top_k or 5), len(self.corpus)))
        query_vector = encode_query(query).astype(np.float32)

        if self.index is not None:
            scores, indices = self.index.search(np.asarray([query_vector], dtype=np.float32), top_k)
            pairs = list(zip(indices[0].tolist(), scores[0].tolist()))
        else:
            scores = self.embeddings @ query_vector
            ranked = np.argsort(scores)[::-1][:top_k]
            pairs = [(int(idx), float(scores[idx])) for idx in ranked]

        results = []
        for idx, score in pairs:
            if idx < 0 or idx >= len(self.corpus):
                continue
            doc = self.corpus[idx]
            results.append(_public_doc(doc, score))
        return results

    def _load_or_build(self, force_rebuild: bool) -> None:
        CORPUS_DIR.mkdir(parents=True, exist_ok=True)
        should_build = force_rebuild or not METADATA_PATH.exists() or not EMBEDDINGS_PATH.exists()
        if should_build:
            rebuild_index(self.corpus)

        try:
            self.embeddings = np.load(EMBEDDINGS_PATH).astype(np.float32)
            self.corpus = _read_jsonl(METADATA_PATH)
        except Exception:
            self.embeddings = encode_texts([doc["text"] for doc in self.corpus]).astype(np.float32)

        if self._faiss is not None and INDEX_PATH.exists():
            try:
                self.index = self._faiss.read_index(str(INDEX_PATH))
            except Exception:
                self.index = _build_faiss_index(self.embeddings, self._faiss)
        elif self._faiss is not None:
            self.index = _build_faiss_index(self.embeddings, self._faiss)


def build_retriever(force_rebuild: bool = False) -> DenseRetriever:
    """Build the final dense retriever."""
    return DenseRetriever(force_rebuild=force_rebuild)


def rebuild_index(corpus: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Rebuild and persist metadata, embeddings, and FAISS index if available."""
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    docs = corpus or load_corpus_documents()
    docs = [_normalize_doc(doc, idx) for idx, doc in enumerate(docs)]
    embeddings = encode_texts([doc["text"] for doc in docs]).astype(np.float32)

    np.save(EMBEDDINGS_PATH, embeddings)
    with METADATA_PATH.open("w", encoding="utf-8") as handle:
        for doc in docs:
            handle.write(json.dumps(doc, ensure_ascii=False, default=str) + "\n")

    faiss = _import_faiss()
    faiss_written = False
    if faiss is not None and len(embeddings) > 0:
        index = _build_faiss_index(embeddings, faiss)
        faiss.write_index(index, str(INDEX_PATH))
        faiss_written = True

    return {
        "documents": len(docs),
        "embedding_dim": int(embeddings.shape[1]) if len(embeddings) else EMBEDDING_DIM,
        "metadata_path": str(METADATA_PATH),
        "embeddings_path": str(EMBEDDINGS_PATH),
        "faiss_path": str(INDEX_PATH) if faiss_written else None,
    }


def load_corpus_documents() -> list[dict[str, Any]]:
    """Load final corpus docs, falling back to data/sample_corpus.json."""
    docs: list[dict[str, Any]] = []
    docs.extend(_load_corpus_dir(CORPUS_DIR))
    if not docs:
        docs.extend(_load_sample_corpus())
    docs.extend(_read_jsonl(DYNAMIC_KNOWLEDGE_PATH))
    docs.extend(_read_jsonl(LEGACY_DYNAMIC_KNOWLEDGE_PATH))

    normalized = []
    seen = set()
    for idx, doc in enumerate(docs):
        item = _normalize_doc(doc, idx)
        key = item["source_id"]
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)
    return normalized


def _load_corpus_dir(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    docs: list[dict[str, Any]] = []
    for file_path in sorted(path.iterdir()):
        if file_path.name in {METADATA_PATH.name, DYNAMIC_KNOWLEDGE_PATH.name, "README.md"}:
            continue
        if file_path.suffix.lower() == ".json":
            try:
                payload = json.loads(file_path.read_text(encoding="utf-8"))
                if isinstance(payload, list):
                    docs.extend(payload)
                elif isinstance(payload, dict):
                    docs.append(payload)
            except Exception:
                continue
        elif file_path.suffix.lower() == ".jsonl":
            docs.extend(_read_jsonl(file_path))
        elif file_path.suffix.lower() in {".txt", ".md"}:
            text = file_path.read_text(encoding="utf-8", errors="ignore").strip()
            if text:
                docs.append(
                    {
                        "source_id": file_path.stem,
                        "text": text,
                        "metadata": {"file": str(file_path), "source_type": "file"},
                    }
                )
    return docs


def _load_sample_corpus() -> list[dict[str, Any]]:
    if not SAMPLE_CORPUS_PATH.exists():
        return []
    try:
        payload = json.loads(SAMPLE_CORPUS_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else []
    except Exception:
        return []


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict) and item.get("text"):
                rows.append(item)
    return rows


def _normalize_doc(doc: dict[str, Any], idx: int) -> dict[str, Any]:
    metadata = dict(doc.get("metadata") or {})
    source_id = str(
        doc.get("source_id")
        or doc.get("id")
        or metadata.get("source_id")
        or f"doc_{idx + 1:04d}"
    )
    verified = bool(doc.get("verified", metadata.get("verified", False)))
    metadata.update(
        {
            "source_id": source_id,
            "domain": doc.get("domain", metadata.get("domain", "general")),
            "title": doc.get("title", metadata.get("title")),
            "source": doc.get("source", metadata.get("source", "local")),
            "verified": verified,
        }
    )
    return {
        "source_id": source_id,
        "id": source_id,
        "text": str(doc.get("text") or doc.get("content") or ""),
        "verified": verified,
        "metadata": metadata,
    }


def _public_doc(doc: dict[str, Any], score: float) -> dict[str, Any]:
    normalized = _normalize_doc(doc, 0)
    return {
        "source_id": normalized["source_id"],
        "id": normalized["source_id"],
        "text": normalized["text"],
        "score": round(float(score), 4),
        "verified": bool(normalized["verified"]),
        "metadata": normalized["metadata"],
    }


def _build_faiss_index(embeddings: np.ndarray, faiss: Any):
    index = faiss.IndexFlatIP(int(embeddings.shape[1]))
    index.add(embeddings.astype(np.float32))
    return index


def _import_faiss():
    try:
        import faiss

        return faiss
    except Exception:
        return None
