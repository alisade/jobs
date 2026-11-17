"""Load the course corpus: markdown lessons with front matter, sections under '## ' headings."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "corpus"


@dataclass(frozen=True)
class Section:
    id: str          # "<lesson>-s<n>", n from 1 in document order, e.g. "l4-s2"
    heading: str
    text: str


@dataclass(frozen=True)
class Lesson:
    course: str
    lesson: str
    title: str
    sections: tuple[Section, ...]


def parse_lesson(md: str) -> Lesson:
    _, fm, body = md.split("---", 2)
    meta = dict(line.split(":", 1) for line in fm.strip().splitlines())
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    sections, heading, buf = [], None, []
    for line in body.splitlines():
        if line.startswith("## "):
            if heading is not None:
                sections.append((heading, " ".join(buf).strip()))
            heading, buf = line[3:].strip(), []
        elif heading is not None and line.strip():
            buf.append(line.strip())
    if heading is not None:
        sections.append((heading, " ".join(buf).strip()))
    lid = meta["lesson"]
    return Lesson(meta["course"], lid, meta["title"],
                  tuple(Section(f"{lid}-s{i}", h, t) for i, (h, t) in enumerate(sections, start=1)))


def load_lessons(root: Path = ROOT) -> list[Lesson]:
    return [parse_lesson(p.read_text()) for p in sorted(root.glob("*.md"))]


def load_questions(root: Path = ROOT) -> list[dict]:
    return [json.loads(l) for l in (root / "questions.jsonl").read_text().splitlines() if l.strip()]
