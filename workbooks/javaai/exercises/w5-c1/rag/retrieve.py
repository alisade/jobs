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

        TODO(w5-c1)
        """
        return []
