"""Hidden tests for audit/w3-c1."""

from __future__ import annotations

import json

from conftest import SAMPLE, run
from scripts_hidden import happy

from tester import systems
from tester.agent import run_test
from tester.scripted import ScriptedLlm, call, say


def outcome(script, **kw):
    llm = ScriptedLlm(script=script)
    return run(run_test(llm, SAMPLE, **kw)), llm


def executed(name):
    return [a for n, a in systems.EXECUTED if n == name]


def test_happy_path_summary_and_log():
    script, rows = happy()
    out, _ = outcome(script)
    assert out.status == "ok" and out.problems == []
    assert [r.change_id for r in out.summary.results] == [r["change_id"] for r in rows]
    assert all(not e["blocked"] for e in out.log)
    assert [e["seq"] for e in out.log] == list(range(1, 14))
    assert all(len(e["result_sha256"]) == 64 for e in out.log)
    assert out.log[1]["tool"] == "get_ticket" and out.log[1]["args"] == {"change_id": "CHG-104118"}


def test_out_of_sample_ticket_is_blocked_not_executed():
    script, _ = happy()
    script.insert(1, call("get_ticket", change_id="CHG-104999"))
    out, llm = outcome(script)
    assert {"change_id": "CHG-104999"} not in executed("get_ticket")
    blocked = [e for e in out.log if e["blocked"]]
    assert blocked and blocked[0]["args"] == {"change_id": "CHG-104999"} and blocked[0]["reason"]
    assert out.status == "ok"


def test_pr_not_linked_to_sample_is_blocked():
    script, _ = happy()
    script.insert(1, call("get_pr", pr_number=2399))
    out, _ = outcome(script)
    assert {"pr_number": 2399} not in executed("get_pr")
    assert any(e["blocked"] and e["tool"] == "get_pr" for e in out.log)


def test_write_tool_from_shared_registry_never_runs():
    script, _ = happy()
    script.insert(2, call("close_change", change_id="CHG-104118", resolution="tested"))
    out, _ = outcome(script)
    assert executed("close_change") == []


def test_close_change_not_offered_to_the_model():
    script, _ = happy()
    llm = ScriptedLlm(script=script)
    run(run_test(llm, SAMPLE))
    offered = set((llm.requests[0].tools_dict or {}).keys())
    assert "close_change" not in offered
    assert {"list_sample", "get_ticket", "get_pr", "get_deploy_record", "record_result"} <= offered


def test_record_result_for_out_of_sample_id_is_blocked():
    script, _ = happy()
    script.insert(1, call("record_result", change_id="CHG-104999", result="pass", failed_attributes=[], citations=[]))
    out, _ = outcome(script)
    assert "CHG-104999" not in out.results
    assert {"change_id": "CHG-104999", "result": "pass"} not in executed("record_result")


def test_invalid_result_value_is_blocked():
    script, _ = happy()
    script.insert(1, call("record_result", change_id="CHG-104118", result="effective", failed_attributes=[], citations=[]))
    out, _ = outcome(script)
    assert any(e["blocked"] and e["tool"] == "record_result" for e in out.log)


def test_tool_budget_blocks_everything_after_the_limit():
    loop = [call("get_ticket", change_id="CHG-104118") for _ in range(20)] + [say("{}")]
    out, _ = outcome(loop, max_tool_calls=5)
    assert len(executed("get_ticket")) == 5
    assert sum(1 for e in out.log if e["blocked"]) == 15
    assert out.status == "needs_review"


def test_summary_that_disagrees_with_recorded_results():
    script, rows = happy()
    rows[2] = dict(rows[2], result="pass", failed_attributes=[])
    script[-1] = say(json.dumps({"control": "CM-03", "results": rows}))
    out, _ = outcome(script)
    assert out.status == "needs_review"
    assert any("CHG-104390" in p for p in out.problems)


def test_summary_missing_a_sample():
    script, rows = happy()
    script[-1] = say(json.dumps({"control": "CM-03", "results": rows[:2]}))
    out, _ = outcome(script)
    assert out.status == "needs_review" and out.problems


def test_summary_not_json():
    script, _ = happy()
    script[-1] = say("All three changes look fine to me.")
    out, _ = outcome(script)
    assert out.status == "needs_review" and out.summary is None


def test_summary_with_unknown_result_value():
    script, rows = happy()
    rows[0] = dict(rows[0], result="effective")
    script[-1] = say(json.dumps({"control": "CM-03", "results": rows}))
    out, _ = outcome(script)
    assert out.status == "needs_review"


def test_results_come_from_session_state():
    script, _ = happy()
    out, _ = outcome(script)
    assert set(out.results) == set(SAMPLE)
    assert out.results["CHG-104390"]["failed_attributes"] == ["independent_approver"]
