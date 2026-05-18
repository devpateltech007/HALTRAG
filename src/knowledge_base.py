"""
Knowledge base helpers for local RAG data.

Uploads are treated as retrieval evidence. The model is not retrained.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, List


DEFAULT_CHUNK_WORDS = 140
DEFAULT_OVERLAP_WORDS = 30


@dataclass
class KnowledgeUploadResult:
    chunks_added: int
    corpus_count: int
    corpus_path: str
    chunk_ids: List[str]
    chunks: List[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def slugify(value: str, fallback: str = "upload") -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:48] or fallback


def _sentence_split(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", clean_text(text))
    return [p.strip() for p in parts if len(p.strip()) > 0]


def _word_chunks(words: List[str], max_words: int, overlap_words: int) -> List[str]:
    if not words:
        return []
    chunks: List[str] = []
    step = max(1, max_words - overlap_words)
    for start in range(0, len(words), step):
        part = words[start : start + max_words]
        if part:
            chunks.append(" ".join(part).strip())
        if start + max_words >= len(words):
            break
    return chunks


def chunk_text(
    text: str,
    *,
    max_words: int = DEFAULT_CHUNK_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
) -> List[str]:
    """
    Split uploaded knowledge into compact chunks with light overlap.
    Sentence boundaries are preferred and long sentences fall back to word windows.
    """
    normalized = clean_text(text)
    if not normalized:
        return []

    max_words = max(40, int(max_words))
    overlap_words = max(0, min(int(overlap_words), max_words // 2))
    sentences = _sentence_split(normalized)
    chunks: List[str] = []
    current: List[str] = []
    current_words = 0

    for sentence in sentences:
        words = sentence.split()
        if len(words) > max_words:
            if current:
                chunks.append(" ".join(current).strip())
                current = []
                current_words = 0
            chunks.extend(_word_chunks(words, max_words, overlap_words))
            continue

        if current and current_words + len(words) > max_words:
            chunks.append(" ".join(current).strip())
            overlap_seed: List[str] = []
            if overlap_words:
                overlap_seed = " ".join(current).split()[-overlap_words:]
            current = overlap_seed + [sentence]
            current_words = len(overlap_seed) + len(words)
        else:
            current.append(sentence)
            current_words += len(words)

    if current:
        chunks.append(" ".join(current).strip())

    return [c for c in chunks if c]


def load_corpus(path: str | os.PathLike[str]) -> List[dict[str, Any]]:
    corpus_path = Path(path)
    if not corpus_path.exists():
        return []
    with corpus_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Corpus JSON must be a list of documents.")
    return data


def save_corpus(path: str | os.PathLike[str], corpus: List[dict[str, Any]]) -> None:
    corpus_path = Path(path)
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{corpus_path.name}.",
        suffix=".tmp",
        dir=str(corpus_path.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(corpus, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(tmp_name, corpus_path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def build_chunk_rows(
    text: str,
    *,
    title: str = "Uploaded Knowledge",
    domain: str = "custom",
    source: str = "user_upload",
    max_words: int = DEFAULT_CHUNK_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
) -> List[dict[str, Any]]:
    chunks = chunk_text(text, max_words=max_words, overlap_words=overlap_words)
    title = clean_text(title) or "Uploaded Knowledge"
    domain = clean_text(domain) or "custom"
    source = clean_text(source) or "user_upload"
    source_slug = slugify(title)
    total = len(chunks)
    rows: List[dict[str, Any]] = []

    for idx, chunk in enumerate(chunks, start=1):
        digest = hashlib.sha1(chunk.encode("utf-8")).hexdigest()[:12]
        rows.append(
            {
                "id": f"upload_{source_slug}_{idx:03d}_{digest}",
                "domain": domain,
                "title": f"{title} chunk {idx}",
                "text": chunk,
                "source": source,
                "chunk_index": idx,
                "chunk_count": total,
            }
        )
    return rows


def add_knowledge_text(
    text: str,
    corpus_path: str | os.PathLike[str],
    *,
    title: str = "Uploaded Knowledge",
    domain: str = "custom",
    source: str = "user_upload",
    max_words: int = DEFAULT_CHUNK_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
) -> KnowledgeUploadResult:
    rows = build_chunk_rows(
        text,
        title=title,
        domain=domain,
        source=source,
        max_words=max_words,
        overlap_words=overlap_words,
    )
    if not rows:
        raise ValueError("No usable text found to add.")

    corpus = load_corpus(corpus_path)
    existing_ids = {str(row.get("id", "")) for row in corpus}
    new_rows = [row for row in rows if row["id"] not in existing_ids]
    corpus.extend(new_rows)
    save_corpus(corpus_path, corpus)

    return KnowledgeUploadResult(
        chunks_added=len(new_rows),
        corpus_count=len(corpus),
        corpus_path=str(Path(corpus_path).resolve()),
        chunk_ids=[row["id"] for row in new_rows],
        chunks=new_rows,
    )
