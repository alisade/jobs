"""Offline stand-in for a cross-encoder or the ranking API (given; do not change).

Scores (query, document text) pairs jointly: concept similarity plus exact-term coverage. Slow in real
life (one model call per pair), so only rerank the top N candidates.
"""

from __future__ import annotations

from .embed import cosine, embed
from .text import tokenize


class StubReranker:
    def __init__(self):
        self.pairs_scored = 0

    def score(self, query: str, text: str) -> float:
        self.pairs_scored += 1
        q = set(tokenize(query))
        d = set(tokenize(text))
        exact = len(q & d) / len(q) if q else 0.0
        return 2.0 * cosine(embed(query), embed(text)) + exact
