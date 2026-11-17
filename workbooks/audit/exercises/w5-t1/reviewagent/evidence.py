"""Evidence access: Document Intelligence layout JSON per change under evidence/<change_id>/. Complete."""

from __future__ import annotations

import json
from pathlib import Path


def evidence_files(evidence_dir: str | Path, change_id: str) -> list[Path]:
    return sorted((Path(evidence_dir) / change_id).glob("*.layout.json"))


def load_layout(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def paragraphs(layout: dict) -> list[dict]:
    """[{"page", "paragraph", "text"}] in document order. Text hidden by styling is still text:
    the PDF text layer contains it, so Document Intelligence returns it like any other paragraph."""
    out = []
    for i, p in enumerate(layout.get("paragraphs", [])):
        out.append({"page": p["boundingRegions"][0]["pageNumber"], "paragraph": i, "text": p["content"]})
    return out


def evidence_text(evidence_dir: str | Path, change_id: str) -> str:
    chunks = []
    for f in evidence_files(evidence_dir, change_id):
        for p in paragraphs(load_layout(f)):
            chunks.append(f"[{f.name} p{p['page']} para{p['paragraph']}] {p['text']}")
    return "\n".join(chunks)
