"""Build and load the file-based vector index (index/vectors.json + index/manifest.json)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from policy_rag.chunker import chunk_words
from policy_rag.embedder import get_embedder


def build_index(corpus_dir: str | Path, out_dir: str | Path, embedder: str, chunk_size: int,
                chunk_overlap: int, built_at: str | None = None) -> dict:
    emb = get_embedder(embedder)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    docs = sorted(Path(corpus_dir).glob("*.md"))
    for doc in docs:
        for i, chunk in enumerate(chunk_words(doc.read_text(), chunk_size, chunk_overlap)):
            rows.append({"chunk_id": f"{doc.stem}#{i}", "doc_id": doc.stem, "text": chunk,
                         "vector": [round(x, 6) for x in emb.embed(chunk)]})
    manifest = {
        "embedder": emb.name,
        "dims": emb.dims,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "doc_count": len(docs),
        "chunk_count": len(rows),
        "built_at": built_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (out / "vectors.json").write_text(json.dumps(rows))
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def load_index(index_dir: str | Path) -> tuple[dict, list[dict]]:
    d = Path(index_dir)
    manifest = json.loads((d / "manifest.json").read_text())
    rows = json.loads((d / "vectors.json").read_text())
    return manifest, rows
