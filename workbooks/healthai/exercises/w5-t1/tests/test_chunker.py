from pathlib import Path

from chunking.chunker import chunk_policy
from chunking.evaluate import run

POL = Path(__file__).resolve().parent.parent / "policies"


def test_eval_runs_and_text_queries_hit():
    assert run()["by_kind"]["text"] == 1.0


def test_criteria_rows_are_whole_in_some_chunk():
    md = (POL / "KHP-MP-0101.md").read_text()
    chunks = chunk_policy(md, "KHP-MP-0101")
    rows = [l for l in md.splitlines() if l.startswith("| 2.")]
    for row in rows:
        assert any(row in c.text.splitlines() for c in chunks), f"row split or reflowed: {row[:40]}"


def test_row_queries_recall():
    assert run()["by_kind"]["row"] >= 0.95
