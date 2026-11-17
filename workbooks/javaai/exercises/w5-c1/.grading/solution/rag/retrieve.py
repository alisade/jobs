"""A tiny vector index with metadata filtering (what pgvector or RAG Engine does for you)."""

from __future__ import annotations

from .chunking import Chunk
from .embed import cosine, embed


class Index:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = list(chunks)
        self.vectors = [embed(c.text) for c in self.chunks]

    def search(self, query: str, k: int, course: str) -> list[Chunk]:
        """Top-k chunks by cosine similarity, ties broken by chunk_id, restricted to `course`.

        The course filter is access control (a learner only sees their course), so it must be
        applied before ranking: never return another course's chunk, even if fewer than k match.

        """
        scored = [(cosine(q, v), c.chunk_id, c) for c, v in zip(self.chunks, self.vectors) if c.course == course
                  for q in [self._q(query)]]
        scored.sort(key=lambda t: (-t[0], t[1]))
        return [c for _, _, c in scored[:k]]

    def _q(self, query: str, _cache: dict = {}) -> list[float]:
        if query not in _cache:
            _cache[query] = embed(query)
        return _cache[query]
