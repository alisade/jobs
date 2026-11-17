"""Structure-aware policy chunker: chunks follow headings, tables are split only between rows, and
every table chunk repeats the header row. Each chunk carries its full section path."""

from __future__ import annotations

import re
from dataclasses import dataclass

MAX_WORDS = 120


@dataclass
class Chunk:
    id: str
    policy_id: str
    section_path: str
    text: str
    kind: str = "text"  # "text" | "table"


def _blocks(markdown: str):
    """Yield (path, kind, lines) blocks: runs of table lines or of text lines under one heading."""
    path: list[str] = []
    kind, buf = None, []
    for line in markdown.splitlines():
        m = re.match(r"^(#+)\s+(.*)$", line)
        is_table = line.lstrip().startswith("|")
        if m or (kind == "table" and not is_table) or (kind == "text" and is_table):
            if buf:
                yield " > ".join(path), kind, buf
            kind, buf = None, []
        if m:
            level = len(m.group(1))
            path = path[: level - 1] + [m.group(2).strip()]
            continue
        if not line.strip():
            if kind == "text":
                buf.append("")
            continue
        kind = "table" if is_table else "text"
        buf.append(line)
    if buf:
        yield " > ".join(path), kind, buf


def _words(lines: list[str]) -> int:
    return sum(len(x.split()) for x in lines)


def chunk_policy(markdown: str, policy_id: str, max_words: int = MAX_WORDS) -> list[Chunk]:
    chunks: list[Chunk] = []

    def add(path, kind, lines):
        text = "\n".join(lines).strip()
        if text:
            chunks.append(Chunk(id=f"{policy_id}#{len(chunks)}", policy_id=policy_id,
                                section_path=path or policy_id, text=text, kind=kind))

    for path, kind, lines in _blocks(markdown):
        if kind == "table":
            header, rows = lines[:2], lines[2:]
            cur: list[str] = []
            for row in rows:
                if cur and _words(header + cur + [row]) > max_words:
                    add(path, "table", header + cur)
                    cur = []
                cur.append(row)
            add(path, "table", header + cur)
        else:
            paras = [p for p in "\n".join(lines).split("\n\n") if p.strip()]
            cur = []
            for para in paras:
                if cur and _words(cur + [para]) > max_words:
                    add(path, "text", cur)
                    cur = []
                cur.append(para)
            add(path, "text", cur)
    return chunks
