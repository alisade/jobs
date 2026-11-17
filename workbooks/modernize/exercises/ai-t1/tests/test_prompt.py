from datetime import datetime

from migrate_agent.prompt import build_request, load_skills
from migrate_agent.session import REPO, replay


def test_request_marks_a_cache_breakpoint():
    req = build_request("t", REPO, load_skills(), datetime(2026, 11, 12, 2, 0, 0), [])
    assert any("cache_control" in b for b in req["system"])


def test_second_turn_reads_the_cache():
    rows = replay()
    assert rows[1]["cache_read_input_tokens"] > 0, rows[1]
