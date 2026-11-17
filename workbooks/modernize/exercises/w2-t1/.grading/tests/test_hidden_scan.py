import io
from contextlib import redirect_stdout
from pathlib import Path

import scan_db

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "repo"
HITS = scan_db.scan(REPO)
BATCH_ONLY = {"LOSS_TRIANGLE", "IBNR_FACTOR", "REINS_TREATY", "BORDEREAU_RUN", "IBNR_RESULT"}


def run_main(*argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        scan_db.main([str(REPO), *argv])
    return buf.getvalue()


def test_summary_is_complete():
    s = scan_db.summarize(HITS)
    assert len(s) == 14
    assert BATCH_ONLY <= set(s)
    assert s["LOSS_TRIANGLE"]["modules"] == ["reporting-batch"]
    assert s["CLAIM"]["count"] == sum(1 for h in HITS if h.table == "CLAIM")
    assert sorted(s["RESERVE_LINE"]["modules"]) == ["claims-core", "reporting-batch"]


def test_truncation_is_announced():
    out = scan_db.render(HITS, limit=200)
    last = out.splitlines()[-1]
    assert "TRUNCATED" in last
    assert "200" in last and str(len(HITS) - 200) in last


def test_full_page_has_no_marker():
    out = scan_db.render(HITS, limit=len(HITS))
    assert "TRUNCATED" not in out
    assert len(out.splitlines()) == len(HITS) + 1


def test_offset_pages():
    out = scan_db.render(HITS, limit=50, offset=300)
    body = [l for l in out.splitlines() if not l.startswith("#")]
    assert len(body) == len(HITS) - 300
    assert body[0].startswith(f"{HITS[300].path}:{HITS[300].line}")
    assert "TRUNCATED" not in out


def test_default_tool_output_names_every_table_and_module():
    out = run_main()
    for t in scan_db.summarize(HITS):
        assert t in out, f"{t} missing from the default tool output"
    assert "reporting-batch" in out
    assert len(out) < 70000, "keep the default output small enough for a context window"


def test_main_offset_flag():
    out = run_main("--limit", "20", "--offset", "40")
    assert "shown=41-60" in out


def test_skill_tells_the_agent_to_check_coverage():
    sk = (ROOT / "skill/reverse-engineer/SKILL.md").read_text().lower()
    assert "truncat" in sk and "summary" in sk
    assert "offset" in sk
