"""Hidden tests for healthai/w5-t1: structure-aware chunking and restored recall."""

import json
from pathlib import Path

import pytest

from chunking.chunker import chunk_policy
from chunking.evaluate import run

EX = Path(__file__).resolve().parent.parent
POLICIES = sorted((EX / "policies").glob("*.md"))
HEADER = "| Criterion | Requirement | Step therapy |"


@pytest.fixture(scope="module", params=[p.stem for p in POLICIES])
def doc(request):
    md = (EX / "policies" / f"{request.param}.md").read_text()
    return request.param, md, chunk_policy(md, request.param)


def test_every_row_whole_in_exactly_one_chunk(doc):
    pid, md, chunks = doc
    for row in [l for l in md.splitlines() if l.startswith("| 2.")]:
        assert sum(row in c.text.splitlines() for c in chunks) == 1, row[:40]


def test_table_chunks_repeat_header_and_hold_whole_lines(doc):
    _, _, chunks = doc
    tables = [c for c in chunks if "| 2." in c.text]
    assert tables
    for c in tables:
        lines = c.text.splitlines()
        assert lines[0] == HEADER and lines[1].startswith("|---"), c.id
        assert all(l.startswith("|") and l.endswith("|") for l in lines), c.id
        assert c.kind == "table"


def test_section_paths(doc):
    pid, _, chunks = doc
    for c in chunks:
        assert c.section_path.startswith(pid), c.section_path
        if "| 2." in c.text:
            assert c.section_path.endswith("Coverage criteria > Criteria table")
        if "attestation" in c.text:
            assert c.section_path.endswith("Coverage criteria > Documentation")
        if "investigational" in c.text:
            assert c.section_path.endswith("Exclusions")


def test_no_chunk_crosses_a_heading_or_mixes_kinds(doc):
    _, _, chunks = doc
    for c in chunks:
        lines = [l for l in c.text.splitlines() if l.strip()]
        assert not any(l.startswith("#") for l in lines), c.id
        table_lines = sum(l.startswith("|") for l in lines)
        assert table_lines in (0, len(lines)), c.id


def test_size_bound_and_small_budget_splits_between_rows(doc):
    pid, md, chunks = doc
    assert all(len(c.text.split()) <= 120 for c in chunks)
    small = chunk_policy(md, pid, max_words=70)
    tables = [c for c in small if "| 2." in c.text]
    assert len(tables) >= 3
    for c in tables:
        assert c.text.splitlines()[0] == HEADER
    rows = [l for l in md.splitlines() if l.startswith("| 2.")]
    assert all(sum(r in c.text.splitlines() for c in small) == 1 for r in rows)


def test_nothing_lost(doc):
    _, md, chunks = doc
    body = " ".join(c.text for c in chunks)
    for line in md.splitlines():
        if line.strip() and not line.startswith("#") and not line.startswith("|---") and line != HEADER:
            assert " ".join(line.split()) in " ".join(body.split()), line[:40]


def test_recall_restored():
    r = run()
    assert r["recall@5"] >= 0.95 and r["by_kind"]["row"] == 1.0, r


def test_findings():
    f = json.loads((EX / "findings.json").read_text())
    assert "chunk" in f["root_cause_component"].lower()
    assert "embed" in f["red_herring"].lower()
    assert f["recall_at_5_before"] == pytest.approx(0.667, abs=0.01)
    assert f["recall_at_5_after"] >= 0.95
    assert len(f["evidence_query_ids"]) >= 2
