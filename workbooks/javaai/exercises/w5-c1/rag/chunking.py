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

    TODO(w5-c1)
    """
    return []


def heading_chunks(lesson: Lesson, max_words: int = 120) -> list[Chunk]:
    """One chunk per section: "<lesson title> - <heading>: <section text>". A section longer than
    `max_words` words is split into consecutive pieces of at most `max_words` words, each carrying
    the same prefix and section_id.

    TODO(w5-c1)
    """
    return []
