"""Two chunking strategies to compare. Every chunk keeps the metadata retrieval and citations need."""

from __future__ import annotations

from dataclasses import dataclass

from .corpus import Lesson


@dataclass(frozen=True)
class Chunk:
    chunk_id: str      # unique, stable: "<strategy>:<lesson>:<n>"
    course: str
    lesson: str
    section_id: str    # the section this chunk cites
    text: str


def fixed_chunks(lesson: Lesson, size: int = 40, overlap: int = 10) -> list[Chunk]:
    """Fixed windows of `size` words with `overlap` words shared between neighbours, over the whole
    lesson text (section bodies concatenated in order, headings dropped). A chunk cites the section
    that contributes the most of its words (ties: the earlier section).

    """
    words: list[tuple[str, str]] = [(w, s.id) for s in lesson.sections for w in s.text.split()]
    if size <= overlap:
        raise ValueError("size must be larger than overlap")
    step = size - overlap
    out: list[Chunk] = []
    start = 0
    n = 0
    while start < len(words):
        window = words[start:start + size]
        counts: dict[str, int] = {}
        for _, sid in window:
            counts[sid] = counts.get(sid, 0) + 1
        order = [s.id for s in lesson.sections]
        best = max(counts, key=lambda sid: (counts[sid], -order.index(sid)))
        out.append(Chunk(f"fixed:{lesson.lesson}:{n}", lesson.course, lesson.lesson, best, " ".join(w for w, _ in window)))
        n += 1
        if start + size >= len(words):
            break
        start += step
    return out


def heading_chunks(lesson: Lesson, max_words: int = 120) -> list[Chunk]:
    """One chunk per section: "<lesson title> - <heading>: <section text>". A section longer than
    `max_words` words is split into consecutive pieces of at most `max_words` words, each carrying
    the same prefix and section_id.

    """
    out: list[Chunk] = []
    n = 0
    for s in lesson.sections:
        prefix = f"{lesson.title} - {s.heading}: "
        words = s.text.split()
        for i in range(0, max(len(words), 1), max_words):
            out.append(Chunk(f"heading:{lesson.lesson}:{n}", lesson.course, lesson.lesson, s.id,
                             prefix + " ".join(words[i:i + max_words])))
            n += 1
    return out
