"""Query path: embed the question and return the most similar chunks."""
from __future__ import annotations

from pathlib import Path

import yaml

from policy_rag.embedder import get_embedder
from policy_rag.index import load_index


class IndexMismatchError(RuntimeError):
    """The query path cannot safely use this index."""


class Retriever:
    def __init__(self, index_dir: str | Path, query_embedder: str, top_k: int = 3, min_score: float = 0.0):
        self.manifest, self.rows = load_index(index_dir)
        indexed_with = self.manifest.get("embedder")
        if query_embedder != indexed_with:
            raise IndexMismatchError(
                f"index {index_dir} was built with embedder {indexed_with!r} but the query path is "
                f"configured for {query_embedder!r}; vectors from different embedders are not comparable. "
                f"Set query_embedder to {indexed_with!r} or rebuild the index."
            )
        self.embedder = get_embedder(query_embedder)
        if self.manifest.get("dims") != self.embedder.dims:
            raise IndexMismatchError(
                f"index dims {self.manifest.get('dims')} != embedder {query_embedder} dims {self.embedder.dims}"
            )
        self.top_k = top_k
        self.min_score = min_score

    @classmethod
    def from_config(cls, config_path: str | Path) -> "Retriever":
        path = Path(config_path)
        cfg = yaml.safe_load(path.read_text())
        root = path.resolve().parent.parent
        index_dir = Path(cfg["index_dir"])
        if not index_dir.is_absolute():
            index_dir = root / index_dir
        return cls(index_dir, cfg["query_embedder"], cfg.get("top_k", 3), cfg.get("min_score", 0.0))

    def search(self, query: str, k: int | None = None) -> list[dict]:
        q = self.embedder.embed(query)
        scored = []
        for row in self.rows:
            score = sum(a * b for a, b in zip(q, row["vector"]))
            if score >= self.min_score:
                scored.append({"chunk_id": row["chunk_id"], "doc_id": row["doc_id"], "score": round(score, 4)})
        scored.sort(key=lambda r: (-r["score"], r["chunk_id"]))
        return scored[: (k or self.top_k) * 3]

    def top_docs(self, query: str, k: int | None = None) -> list[str]:
        out: list[str] = []
        for hit in self.search(query, k):
            if hit["doc_id"] not in out:
                out.append(hit["doc_id"])
        return out[: k or self.top_k]
