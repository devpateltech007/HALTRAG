"""
BM25 lexical retriever using rank_bm25.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, List, Sequence, Tuple

from rank_bm25 import BM25Okapi


def tokenize_bm25(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


@dataclass
class RetrievedDoc:
    doc_id: str
    score: float
    title: str
    text: str
    domain: str = ""
    meta: dict | None = None


class BM25Retriever:
    def __init__(
        self,
        corpus: Sequence[dict[str, Any]],
        text_fields: Tuple[str, ...] = ("title", "text"),
    ):
        self.corpus_rows = list(corpus)
        self.text_fields = text_fields
        self._tokenized: List[List[str]] = []
        for row in self.corpus_rows:
            blob = " ".join(str(row.get(f, "") or "") for f in text_fields)
            self._tokenized.append(tokenize_bm25(blob))
        self._bm25 = BM25Okapi(self._tokenized)

    @classmethod
    def from_json(cls, path: str) -> "BM25Retriever":
        abs_path = os.path.abspath(path)
        with open(abs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Corpus JSON must be a list of documents.")
        return cls(data)

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedDoc]:
        q_tokens = tokenize_bm25(query)
        scores = self._bm25.get_scores(q_tokens)
        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]
        out: List[RetrievedDoc] = []
        for idx, score in ranked:
            row = self.corpus_rows[idx]
            rid = row.get("id", str(idx))
            out.append(
                RetrievedDoc(
                    doc_id=str(rid),
                    score=float(score),
                    title=str(row.get("title", "")),
                    text=str(row.get("text", "")),
                    domain=str(row.get("domain", "")),
                    meta={k: v for k, v in row.items() if k not in ("title", "text", "id", "domain")},
                )
            )
        return out

    def passages_for_prompt(self, retrieved: Sequence[RetrievedDoc], max_chars: int = 6000) -> str:
        parts: List[str] = []
        used = 0
        for r in retrieved:
            block = f"[{r.doc_id}] {r.title}\n{r.text}".strip()
            if used + len(block) > max_chars:
                remain = max_chars - used
                if remain > 80:
                    parts.append(block[:remain] + "...")
                break
            parts.append(block)
            used += len(block) + 2
        return "\n\n".join(parts)


def load_json_corpus(path: str) -> List[dict[str, Any]]:
    with open(os.path.abspath(path), "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Corpus JSON must be a list of documents.")
    return data
