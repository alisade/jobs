"""Visible tests for ai-c1: two happy-path recordings."""
from triage.agent import run_triage
from triage.llm import FakeLLM


def test_s02_oom_triage_note():
    res = run_triage("ALR-10412", FakeLLM.from_scenario("s02"))
    assert res.status == "ok"
    assert res.note.severity == "SEV3" and "oom" in res.note.suspected_cause.lower()


def test_s01_evidence_is_grounded():
    res = run_triage("ALR-10411", FakeLLM.from_scenario("s01"))
    executed = {c["id"] for c in res.tool_calls if c["executed"]}
    assert res.status == "ok" and all(e.tool_use_id in executed for e in res.note.evidence)
