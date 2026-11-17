import json
import shutil
from pathlib import Path

import pytest

from ingest import eval as ev
from ingest.build_index import ingest, read_index, write_index

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
QUESTIONS = [json.loads(l) for l in (CORPUS / "questions.jsonl").read_text().splitlines() if l.strip()]


def front_matter_lesson(path: Path) -> str:
    for line in path.read_text().splitlines():
        if line.startswith("lesson:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(path)


def test_lesson_ids_come_from_front_matter():
    rows = ingest(CORPUS)
    by_heading = {r.heading: r for r in rows}
    assert by_heading["How vaccines work"].section_id == "l2-s2"
    assert by_heading["How this course works"].section_id == "l0-s1"
    assert by_heading["Stewardship"].lesson == "l3"


def test_file_names_and_order_do_not_matter(tmp_path):
    # rename files so they sort differently: ids must not move
    names = {"00-welcome.md": "zz-welcome.md", "01-transmission.md": "b.md", "02-vaccines.md": "a.md", "03-antibiotics.md": "c.md"}
    for old, new in names.items():
        shutil.copy(CORPUS / old, tmp_path / new)
    a = sorted((r.chunk_id, r.section_id, r.heading) for r in ingest(CORPUS))
    b = sorted((r.chunk_id, r.section_id, r.heading) for r in ingest(tmp_path))
    assert a == b


def test_missing_lesson_id_is_an_error(tmp_path):
    (tmp_path / "x.md").write_text("---\ncourse: bio-210\ntitle: No id\n---\n\n## A\n\ntext\n")
    with pytest.raises(Exception):
        ingest(tmp_path)


def test_duplicate_lesson_id_is_an_error(tmp_path):
    shutil.copy(CORPUS / "02-vaccines.md", tmp_path / "a.md")
    shutil.copy(CORPUS / "02-vaccines.md", tmp_path / "b.md")
    with pytest.raises(Exception):
        ingest(tmp_path)


def test_recall_is_back():
    rows = ingest(CORPUS)
    assert ev.recall_at_3(rows, QUESTIONS) >= 0.9


def test_reingest_is_idempotent(tmp_path):
    out = tmp_path / "index.jsonl"
    write_index(ingest(CORPUS), out)
    first = out.read_text()
    write_index(ingest(CORPUS), out)
    assert out.read_text() == first
    assert len({r.chunk_id for r in read_index(out)}) == len(read_index(out)), "chunk ids must be unique"


def test_every_section_is_still_indexed():
    assert len(ingest(CORPUS)) == 13
