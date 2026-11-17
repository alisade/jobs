"""Hybrid retrieval: BM25 + hashing-vector cosine, fused with reciprocal rank fusion."""

from __future__ import annotations

import math
import re
import zlib
from collections import Counter

TOKEN = re.compile(r"[a-z0-9]+(?:[-:.][a-z0-9]+)*")


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def bm25_scores(docs: list[str], query: str, k1: float = 1.5, b: float = 0.75) -> list[float]:
    raise NotImplementedError("TODO: README task 2 (bm25_scores)")


def hash_vector(text: str, dim: int = 512) -> list[float]:
    raise NotImplementedError("TODO: README task 2 (hash_vector)")


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def rrf(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    raise NotImplementedError("TODO: README task 2 (rrf)")


def _ranked(ids: list[str], scores: list[float]) -> list[str]:
    pairs = [(cid, s) for cid, s in zip(ids, scores) if s > 0]
    return [cid for cid, _ in sorted(pairs, key=lambda kv: (-kv[1], kv[0]))]


def hybrid_search(chunks: list, query: str, top_k: int = 8, k: int = 60) -> list[tuple[object, float]]:
    raise NotImplementedError("TODO: README task 2 (hybrid_search)")
