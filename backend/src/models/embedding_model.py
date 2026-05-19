"""Embedding model wrapper for dense retrieval and grounding checks.

The preferred path uses sentence-transformers/all-MiniLM-L6-v2 on CUDA when
available. If the dependency or local model weights are unavailable, the module
falls back to deterministic hashed embeddings so the local demo still runs.
"""

from __future__ import annotations

import hashlib
import os
import re
from functools import lru_cache
from typing import Iterable

import numpy as np


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def encode_texts(texts: Iterable[str]) -> np.ndarray:
    """Encode texts into normalized vectors.

    Returns a float32 matrix with one row per input text. The function never
    raises because a model cannot be loaded; it uses a deterministic local
    fallback in that case.
    """
    text_list = [str(text or "") for text in texts]
    if not text_list:
        return np.zeros((0, EMBEDDING_DIM), dtype=np.float32)

    model = _load_sentence_transformer()
    if model is not None:
        try:
            vectors = model.encode(
                text_list,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            return np.asarray(vectors, dtype=np.float32)
        except Exception:
            pass

    return _hash_embeddings(text_list)


def encode_query(query: str) -> np.ndarray:
    """Encode one query into a normalized vector."""
    return encode_texts([query])[0]


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float | np.ndarray:
    """Compute cosine similarity for vectors or matrices."""
    left = np.asarray(a, dtype=np.float32)
    right = np.asarray(b, dtype=np.float32)

    if left.ndim == 1 and right.ndim == 1:
        denom = float(np.linalg.norm(left) * np.linalg.norm(right))
        if denom == 0.0:
            return 0.0
        return float(np.dot(left, right) / denom)

    left_2d = np.atleast_2d(left)
    right_2d = np.atleast_2d(right)
    left_norm = np.linalg.norm(left_2d, axis=1, keepdims=True)
    right_norm = np.linalg.norm(right_2d, axis=1, keepdims=True)
    left_norm[left_norm == 0.0] = 1.0
    right_norm[right_norm == 0.0] = 1.0
    return (left_2d / left_norm) @ (right_2d / right_norm).T


@lru_cache(maxsize=1)
def _load_sentence_transformer():
    try:
        import torch
        from sentence_transformers import SentenceTransformer

        device = "cuda" if torch.cuda.is_available() else "cpu"
        local_only = os.getenv("HALT_RAG_ALLOW_MODEL_DOWNLOAD", "0").lower() not in {
            "1",
            "true",
            "yes",
        }
        return SentenceTransformer(MODEL_NAME, device=device, local_files_only=local_only)
    except Exception:
        return None


def _hash_embeddings(texts: list[str], dim: int = EMBEDDING_DIM) -> np.ndarray:
    vectors = np.zeros((len(texts), dim), dtype=np.float32)
    for row, text in enumerate(texts):
        for token in _tokens(text):
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            column = int(digest, 16) % dim
            vectors[row, column] += 1.0
        norm = np.linalg.norm(vectors[row])
        if norm > 0.0:
            vectors[row] /= norm
    return vectors


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?", text.lower())
