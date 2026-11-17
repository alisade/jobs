from pathlib import Path

import scan_db

REPO = Path(__file__).resolve().parent.parent / "repo"


def test_scan_reads_sql_files_too():
    tables = {h.table for h in scan_db.scan(REPO)}
    assert "IBNR_RESULT" in tables


def test_hits_have_file_and_line():
    h = scan_db.scan(REPO)[0]
    assert (REPO / h.path).is_file() and h.line >= 1


def test_render_states_the_total():
    hits = scan_db.scan(REPO)
    first = scan_db.render(hits, limit=10).splitlines()[0]
    assert f"total={len(hits)}" in first
