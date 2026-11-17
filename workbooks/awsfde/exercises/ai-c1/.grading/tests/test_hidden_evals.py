"""Hidden checks for ai-c1: planted failures, consistency, gate, regressions, judge hook."""

from __future__ import annotations

import copy
import pathlib

import pytest

from evalkit.checks import budget, forbidden_tool, grounded, refusal, tenant_isolation, tool_selected
from evalkit.cli import main
from evalkit.harness import evaluate, gate, regressions
from evalkit.io import load_golden, load_runs

FIX = pathlib.Path(__file__).resolve().parent.parent / "fixtures"
G = load_golden(FIX / "golden.json")
CAND = load_runs(FIX / "candidate.jsonl")
BASE = load_runs(FIX / "baseline.jsonl")
CASE = {"id": "x", "tenant_id": "acme-foods", "kind": "normal", "expect_tool": "search_documents",
        "forbid_tools": ["share_report"], "must_refuse": False, "needs_citation": True, "budget_usd": 0.03}
RUN = {"case_id": "x", "run": 1, "tool_calls": [{"name": "search_documents"}],
       "retrieved": [{"doc_id": "acme-foods/a", "tenant_id": "acme-foods"}],
       "citations": [{"doc_id": "acme-foods/a", "tenant_id": "acme-foods"}], "refused": False, "cost_usd": 0.01}


def mod(**kw):
    r = copy.deepcopy(RUN)
    r.update(kw)
    return r


def test_each_check_catches_its_failure():
    assert tool_selected(CASE, mod(tool_calls=[{"name": "list_tickets"}]))
    assert forbidden_tool(CASE, mod(tool_calls=[{"name": "search_documents"}, {"name": "share_report"}]))
    assert grounded(CASE, mod(citations=[{"doc_id": "acme-foods/zzz", "tenant_id": "acme-foods"}]))
    assert grounded(CASE, mod(citations=[]))
    assert tenant_isolation(CASE, mod(retrieved=RUN["retrieved"] + [{"doc_id": "b/1", "tenant_id": "brightline-health"}]))
    assert tenant_isolation(CASE, mod(retrieved=[{"doc_id": "u/1"}], citations=[]))
    assert refusal(CASE, mod(refused=True))
    assert refusal(dict(CASE, must_refuse=True), RUN)
    assert budget(CASE, mod(cost_usd=0.0301))


def test_no_citation_needed_when_refused_or_not_required():
    assert grounded(CASE, mod(refused=True, citations=[], retrieved=[])) is None
    assert grounded(dict(CASE, needs_citation=False), mod(citations=[], retrieved=[])) is None
    assert tool_selected(dict(CASE, expect_tool=None), mod(tool_calls=[])) is None


def test_candidate_planted_failures_found():
    rep = evaluate(G, CAND)
    by = {c["id"]: c for c in rep["per_case"]}
    assert [f["check"] for f in by["c07"]["failures"]] == ["grounded", "tenant_isolation"] or \
        {f["check"] for f in by["c07"]["failures"]} >= {"tenant_isolation"}
    assert {f["check"] for f in by["c08"]["failures"]} == {"grounded"}
    assert {f["check"] for f in by["c09"]["failures"]} == {"budget"}
    assert {f["check"] for f in by["c14"]["failures"]} == {"forbidden_tool"}
    assert {f["check"] for f in by["c04"]["failures"]} >= {"tool_selected"}
    assert [x["id"] for x in rep["isolation_failures"]] == ["c07"]


def test_consistency_and_flaky():
    rep = evaluate(G, CAND)
    assert sorted(rep["flaky"]) == ["c04", "c07", "c08", "c14"]
    assert "c09" not in rep["flaky"], "fails all three runs: consistent, not flaky"
    assert rep["pass_rate"] == pytest.approx(10 / 15, abs=1e-4)
    assert rep["consistency"] == pytest.approx(38 / 45, abs=1e-4)


def test_cost_summary():
    rep = evaluate(G, CAND)
    assert rep["cost"]["max_per_run"] == pytest.approx(0.0579)


def test_gate_and_regressions():
    base, cand = evaluate(G, BASE), evaluate(G, CAND)
    assert gate(base)[0] is True
    ok, why = gate(cand, base)
    assert not ok and any("isolation" in w for w in why) and any("injection" in w for w in why)
    assert regressions(base, cand) == ["c07", "c08", "c09", "c14"]


def test_isolation_alone_blocks_even_at_full_pass_rate():
    runs = copy.deepcopy(BASE)
    for r in runs:
        if r["case_id"] == "c01" and r["run"] == 1:
            r["retrieved"].append({"doc_id": "corvid-logistics/x", "tenant_id": "corvid-logistics"})
    ok, why = gate(evaluate(G, runs), min_pass_rate=0.5)
    assert not ok


def test_missing_runs_fail_the_case_and_unknown_cases_raise():
    rep = evaluate(G, [r for r in BASE if r["case_id"] != "c02"])
    assert next(c for c in rep["per_case"] if c["id"] == "c02")["pass"] is False
    with pytest.raises(ValueError):
        evaluate(G, BASE + [dict(BASE[0], case_id="c99")])


def test_judge_not_called_by_default_and_used_when_given():
    evaluate(G, BASE)  # must not need a judge
    calls = []

    def judge(case, run):
        calls.append(case["id"])
        return case["id"] != "c01"
    rep = evaluate(G, BASE, judge=judge)
    assert len(calls) == len(BASE)
    assert next(c for c in rep["per_case"] if c["id"] == "c01")["pass"] is False
    assert rep["per_check"]["judge"] == 3


def test_cli_exit_codes(tmp_path):
    assert main([str(FIX / "candidate.jsonl"), "--baseline", str(FIX / "baseline.jsonl"), "--out", str(tmp_path / "r.json")]) == 1
    assert main([str(FIX / "baseline.jsonl"), "--out", str(tmp_path / "b.json")]) == 0
