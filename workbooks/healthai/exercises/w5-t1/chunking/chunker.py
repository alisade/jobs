"""Policy chunker v2 (release 2026.11): fixed-size word windows with overlap.

v1 chunked per section and produced uneven chunk sizes; v2 makes every chunk the same size so the
embedding batch job is predictable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

WINDOW = 60
OVERLAP = 10
MAX_WORDS = 120  # used by v1; kept for the structure-aware chunker


@dataclass
class Chunk:
    id: str
    policy_id: str
    section_path: str
    text: str
    kind: str = "text"  # "text" | "table"


def _headings(markdown: str) -> list[tuple[int, str]]:
    """(word offset, heading path) for every heading, in order."""
    out, path, offset = [], [], 0
    for line in markdown.splitlines():
        m = re.match(r"^(#+)\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            path = path[: level - 1] + [m.group(2).strip()]
            out.append((offset, " > ".join(path)))
        offset += len(line.split())
    return out


def chunk_policy(markdown: str, policy_id: str) -> list[Chunk]:
    words = markdown.split()
    heads = _headings(markdown)
    chunks, start, n = [], 0, 0
    while start < len(words):
        end = min(start + WINDOW, len(words))
        path = policy_id
        for off, p in heads:
            if off <= start:
                path = p
        chunks.append(Chunk(id=f"{policy_id}#{n}", policy_id=policy_id, section_path=path,
                            text=" ".join(words[start:end])))
        n += 1
        if end == len(words):
            break
        start = end - OVERLAP
    return chunks
