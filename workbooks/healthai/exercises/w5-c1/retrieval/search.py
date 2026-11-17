"""BM25, dense search, reciprocal rank fusion, metadata filters and rerank. Finish the TODOs (README)."""

from __future__ import annotations

import math  # noqa: F401
from collections import Counter
from datetime import date  # noqa: F401

from .embed import cosine, embed
from .text import tokenize

RRF_K = 60


class BM25Index:
    """TODO: real Okapi BM25 (k1, b, idf = ln(1 + (N - df + 0.5) / (df + 0.5))). Today: term overlap count."""

    def __init__(self, docs: list[dict], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.ids = [d["id"] for d in docs]
        self.tf = [Counter(tokenize(d["text"])) for d in docs]

    def search(self, query: str, k: int = 10, allowed: set[str] | None = None) -> list[tuple[str, float]]:
        q = set(tokenize(query))
        hits = [(self.ids[i], float(len(q & set(tf)))) for i, tf in enumerate(self.tf)]
        hits = [h for h in hits if h[1] > 0]
        hits.sort(key=lambda h: (-h[1], h[0]))
        return hits[:k]


class DenseIndex:
    def __init__(self, docs: list[dict]):
        self.ids = [d["id"] for d in docs]
        self.vecs = [embed(d["text"]) for d in docs]

    def search(self, query: str, k: int = 10, allowed: set[str] | None = None) -> list[tuple[str, float]]:
        q = embed(query)
        hits = [(self.ids[i], cosine(q, v)) for i, v in enumerate(self.vecs) if allowed is None or self.ids[i] in allowed]
        hits = [h for h in hits if h[1] > 0]
        hits.sort(key=lambda h: (-h[1], h[0]))
        return hits[:k]


def rrf(ranked_lists: list[list[str]], k: int = RRF_K) -> list[tuple[str, float]]:
    """TODO: reciprocal rank fusion, score(d) = sum over lists of 1 / (k + rank), rank starting at 1."""
    return [(d, 0.0) for d in ranked_lists[0]] if ranked_lists else []


def allowed_ids(docs: list[dict], lob: str | None, as_of: str | None) -> set[str]:
    """TODO: ids allowed for this line of business and as-of date (effective_from <= as_of < effective_to)."""
    return {d["id"] for d in docs}


class HybridRetriever:
    def __init__(self, docs: list[dict], reranker=None, rerank_top_n: int = 20, candidates: int = 50):
        self.docs = docs
        self.by_id = {d["id"]: d for d in docs}
        self.bm25 = BM25Index(docs)
        self.dense = DenseIndex(docs)
        self.reranker = reranker
        self.rerank_top_n = rerank_top_n
        self.candidates = candidates

    def retrieve(self, query: str, lob: str | None = None, as_of: str | None = None, k: int = 10,
                 mode: str = "hybrid", rerank: bool = False) -> list[str]:
        allowed = allowed_ids(self.docs, lob, as_of)  # filter BEFORE ranking
        n = self.candidates
        if mode == "bm25":
            ranked = [d for d, _ in self.bm25.search(query, n, allowed)]
        elif mode == "dense":
            ranked = [d for d, _ in self.dense.search(query, n, allowed)]
        elif mode == "hybrid":
            ranked = [d for d, _ in rrf([[d for d, _ in self.bm25.search(query, n, allowed)],
                                         [d for d, _ in self.dense.search(query, n, allowed)]])]
        else:
            raise ValueError(f"unknown mode {mode!r}")
        # TODO: rerank the top rerank_top_n candidates with self.reranker.score(query, text)
        return ranked[:k]
