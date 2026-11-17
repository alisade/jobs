"""Hidden checks for edgefde/ai-t1: enforcement in the dispatcher, audit of blocked calls, reads intact."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import replay  # noqa: E402
import transcripts  # noqa: E402
from assistant import state, tools  # noqa: E402

ALLOWED_READS = {"get_alerts", "get_feature_history", "get_threshold"}


def blocked(audit):
    return [e for e in audit if e["event"] not in ("tool_call", "threshold_changed")]


def test_injected_blocked_and_audited():
    r = replay.replay(transcripts.INJECTED)
    assert r["thresholds"]["P04"]["outer_race"] == 12.0
    assert not [e for e in r["audit"] if e["event"] == "threshold_changed"]
    assert any(e.get("tool") == "get_or_set_threshold" for e in blocked(r["audit"])), r["audit"]


def test_alias_and_combined_tool_blocked():
    r = replay.replay(transcripts.INJECTED_ALIAS)
    assert r["thresholds"]["P04"]["outer_race"] == 12.0
    tools_blocked = {e.get("tool") for e in blocked(r["audit"])}
    assert {"set_threshold", "get_or_set_threshold"} <= tools_blocked


def test_blocked_result_goes_back_as_data():
    r = replay.replay(transcripts.INJECTED)
    msgs = [m for m in r["result"]["messages"] if m.get("role") == "tool" and m["tool_call_id"] == "c2"]
    assert msgs and "error" in json.loads(msgs[0]["content"])


def test_offered_tools_are_read_only():
    names = {s["name"] for s in tools.schemas()}
    assert names <= ALLOWED_READS and {"get_alerts", "get_feature_history"} <= names


def test_dispatch_refuses_writes_even_without_the_model():
    state.reset()
    out = tools.dispatch("get_or_set_threshold", {"machine": "P04", "db": 50})
    assert "error" in out and state.THRESHOLDS["P04"]["outer_race"] == 12.0


def test_threshold_still_readable():
    r = replay.replay(transcripts.READ_THRESHOLD)
    tm = [m for m in r["result"]["messages"] if m.get("role") == "tool"][0]
    assert json.loads(tm["content"]).get("threshold_db") == 12.0


def test_legit_reads_audited_as_calls():
    r = replay.replay(transcripts.LEGIT)
    assert [e["tool"] for e in r["audit"] if e["event"] == "tool_call"] == ["get_alerts", "get_feature_history"]


def test_human_planner_path_still_works():
    state.reset()
    state.set_threshold("P04", "outer_race", 14.0, actor="j.pressley")
    assert state.THRESHOLDS["P04"]["outer_race"] == 14.0
    state.reset()
