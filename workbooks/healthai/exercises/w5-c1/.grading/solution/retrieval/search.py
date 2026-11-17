"""BM25, dense search, reciprocal rank fusion, metadata filters and rerank."""

from __future__ import annotations

import math
from collections import Counter
from datetime import date

from .embed import cosine, embed
from .text import tokenize

RRF_K = 60


class BM25Index:
    def __init__(self, docs: list[dict], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.ids = [d["id"] for d in docs]
        self.tf = [Counter(tokenize(d["text"])) for d in docs]
        self.len = [sum(tf.values()) for tf in self.tf]
        self.avgdl = sum(self.len) / len(self.len) if self.len else 0.0
        df: Counter = Counter()
        for tf in self.tf:
            df.update(tf.keys())
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def score(self, query: str, i: int) -> float:
        s, tf, dl = 0.0, self.tf[i], self.len[i]
        for t in tokenize(query):
            f = tf.get(t, 0)
            if f:
                s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return s

    def search(self, query: str, k: int = 10, allowed: set[str] | None = None) -> list[tuple[str, float]]:
        hits = [(self.ids[i], self.score(query, i)) for i in range(len(self.ids))
                if allowed is None or self.ids[i] in allowed]
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
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def allowed_ids(docs: list[dict], lob: str | None, as_of: str | None) -> set[str]:
    day = date.fromisoformat(as_of) if as_of else None
    out = set()
    for d in docs:
        if lob and lob not in d["lobs"]:
            continue
        if day:
            if date.fromisoformat(d["effective_from"]) > day:
                continue
            if d.get("effective_to") and date.fromisoformat(d["effective_to"]) <= day:
                continue
        out.add(d["id"])
    return out


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
        if rerank and self.reranker is not None:
            head = ranked[: self.rerank_top_n]
            scored = sorted(head, key=lambda i: (-self.reranker.score(query, self.by_id[i]["text"]), head.index(i)))
            ranked = scored + ranked[self.rerank_top_n:]
        return ranked[:k]
