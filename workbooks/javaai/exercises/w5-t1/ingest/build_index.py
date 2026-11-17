"""Course ingestion job (Cloud Run job `course-ingest`): markdown lessons -> section chunks -> index.

Run by Cloud Build on every merge to the course-content repo. Writes index rows that the tutor's
search_course tool queries (pgvector table course_chunks in production; a JSONL file here).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .embed import embed

EMBEDDING_MODEL = "text-embedding-005"  # bumped from text-embedding-004 in release 3.2


@dataclass(frozen=True)
class Row:
    chunk_id: str
    course: str
    lesson: str
    section_id: str
    heading: str
    text: str
    embedding_model: str


def split_front_matter(md: str) -> tuple[dict, str]:
    if not md.startswith("---"):
        return {}, md
    _, fm, body = md.split("---", 2)
    meta = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, body


def sections(body: str) -> list[tuple[str, str]]:
    out, heading, buf = [], None, []
    for line in body.splitlines():
        if line.startswith("## "):
            if heading is not None:
                out.append((heading, " ".join(buf).strip()))
            heading, buf = line[3:].strip(), []
        elif heading is not None and line.strip():
            buf.append(line.strip())
    if heading is not None:
        out.append((heading, " ".join(buf).strip()))
    return out


def ingest(corpus: Path) -> list[Row]:
    rows: list[Row] = []
    # lessons are numbered in the order the authors file them (01-, 02-, ...)
    for n, path in enumerate(sorted(corpus.glob("*.md")), start=1):
        meta, body = split_front_matter(path.read_text())
        lesson_id = f"l{n}"
        for i, (heading, text) in enumerate(sections(body), start=1):
            sid = f"{lesson_id}-s{i}"
            rows.append(Row(f"{meta.get('course')}:{sid}", meta.get("course", ""), lesson_id, sid, heading,
                            f"{meta.get('title', '')} - {heading}: {text}", EMBEDDING_MODEL))
    return rows


def write_index(rows: list[Row], out: Path) -> None:
    out.write_text("".join(json.dumps(asdict(r)) + "\n" for r in rows))


def read_index(path: Path) -> list[Row]:
    return [Row(**json.loads(l)) for l in path.read_text().splitlines() if l.strip()]


def search(rows: list[Row], query: str, course: str, k: int = 3) -> list[Row]:
    q = embed(query)
    scored = sorted(((sum(a * b for a, b in zip(q, embed(r.text))), r.chunk_id, r) for r in rows if r.course == course),
                    key=lambda t: (-t[0], t[1]))
    return [r for _, _, r in scored[:k]]
