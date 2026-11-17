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
    toks = [tokenize(d) for d in docs]
    n = len(toks)
    if n == 0:
        return []
    avgdl = sum(len(t) for t in toks) / n or 1.0
    df = Counter(term for t in toks for term in set(t))
    q = tokenize(query)
    scores = []
    for t in toks:
        tf = Counter(t)
        s = 0.0
        for term in q:
            if term not in tf:
                continue
            idf = math.log((n - df[term] + 0.5) / (df[term] + 0.5) + 1)
            f = tf[term]
            s += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * len(t) / avgdl))
        scores.append(s)
    return scores


def hash_vector(text: str, dim: int = 512) -> list[float]:
    v = [0.0] * dim
    for tok in tokenize(text):
        v[zlib.crc32(tok.encode()) % dim] += 1.0
    norm = math.sqrt(sum(x * x for x in v))
    return [x / norm for x in v] if norm else v


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def rrf(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    score: dict[str, float] = {}
    for ranking in rankings:
        for rank, cid in enumerate(ranking, start=1):
            score[cid] = score.get(cid, 0.0) + 1.0 / (k + rank)
    return sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))


def _ranked(ids: list[str], scores: list[float]) -> list[str]:
    pairs = [(cid, s) for cid, s in zip(ids, scores) if s > 0]
    return [cid for cid, _ in sorted(pairs, key=lambda kv: (-kv[1], kv[0]))]


def hybrid_search(chunks: list, query: str, top_k: int = 8, k: int = 60) -> list[tuple[object, float]]:
    ids = [c.id for c in chunks]
    by_id = {c.id: c for c in chunks}
    keyword = _ranked(ids, bm25_scores([c.text for c in chunks], query))
    qv = hash_vector(query)
    vector = _ranked(ids, [cosine(qv, hash_vector(c.text)) for c in chunks])
    return [(by_id[cid], s) for cid, s in rrf([keyword, vector], k)[:top_k]]
