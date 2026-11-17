"""Hidden tests for audit/w1-c1. Edge cases and the README requirements."""

from __future__ import annotations

import json

import pytest
from google.genai import types
from pydantic import ValidationError

from controlpilot.attributes import evaluate, overall
from controlpilot.contract import ChangeEvidence, DeployRecord
from controlpilot.extract import build_config, extract
from controlpilot.fake_gemini import FakeClient, call_response, text_response

GOOD = {
    "change_id": "CHG-104118", "pr_number": 2231, "author": "dkwan", "approver": "lpatel",
    "approval_at": "2026-03-04T09:15:00-06:00", "tests_passed": True,
    "citations": [{"source": "ticket", "locator": "approvals[0]", "quote": "CAB approved"}],
}


def good(**over):
    d = json.loads(json.dumps(GOOD))
    d.update(over)
    return d


# ---------------- contract ----------------

def test_contract_accepts_good_and_nulls():
    ChangeEvidence.model_validate(GOOD)
    ChangeEvidence.model_validate(good(approver=None, approval_at=None, tests_passed=None))


@pytest.mark.parametrize("bad", [
    good(conclusion="effective"),
    good(approval_at="2026-03-04T09:15:00"),
    good(change_id="104118"),
    good(citations=[]),
    good(citations=[{"source": "email", "locator": "x", "quote": "y"}]),
    good(citations=[{"source": "ticket", "locator": "x", "quote": ""}]),
    good(pr_number=0),
], ids=["extra-field", "naive-datetime", "bad-change-id", "no-citations", "bad-source", "empty-quote", "pr-zero"])
def test_contract_rejects(bad):
    with pytest.raises(ValidationError):
        ChangeEvidence.model_validate(bad)


@pytest.mark.parametrize("key", ["approver", "approval_at", "tests_passed", "citations"])
def test_contract_requires_every_key(key):
    d = good()
    del d[key]
    with pytest.raises(ValidationError):
        ChangeEvidence.model_validate(d)


# ---------------- config ----------------

def test_build_config():
    cfg = build_config()
    assert cfg.temperature == 0
    assert cfg.response_mime_type == "application/json"
    assert cfg.response_schema is ChangeEvidence
    assert cfg.automatic_function_calling is not None and cfg.automatic_function_calling.disable is True
    decls = {d.name: d for t in cfg.tools for d in (t.function_declarations or [])}
    assert set(decls) == {"get_ticket_approvals", "get_pr_checks"}
    pr = decls["get_pr_checks"].parameters_json_schema
    assert pr["properties"]["pr_number"]["type"] == "integer" and pr["required"] == ["pr_number"]
    assert decls["get_pr_checks"].description
    assert cfg.system_instruction and "data" in str(cfg.system_instruction).lower()


# ---------------- extraction loop ----------------

def test_truncated_response_is_retried(samples, tools, client_for):
    client = client_for("S02")
    res = extract(client, samples["S02"], tools)
    assert res.status == "ok", res.errors
    assert res.attempts == 2
    assert res.usage.calls == 3
    assert res.usage.prompt_tokens == 850 + 900 + 900
    assert res.usage.output_tokens == 20 + 1024 + 120
    retry_req = client.models.requests[2]["contents"]
    last_text = " ".join(p.text or "" for p in retry_req[-1].parts)
    assert "max_tokens" in last_text.lower() or "truncat" in last_text.lower()


def test_extra_field_retry_feeds_back_the_error(samples, tools, client_for):
    client = client_for("S06")
    res = extract(client, samples["S06"], tools)
    assert res.status == "ok" and res.attempts == 2
    retry_req = client.models.requests[2]["contents"]
    last = retry_req[-1]
    assert last.role == "user"
    assert "conclusion" in " ".join(p.text or "" for p in last.parts)


def test_disallowed_tool_is_never_executed(samples, tools, client_for, deploys, directory):
    called = []
    spy = dict(tools)
    spy["close_change"] = lambda **kw: called.append(kw)
    client = client_for("S05")
    res = extract(client, samples["S05"], spy)
    assert called == [], "a tool outside ALLOWED_TOOLS was executed"
    assert res.status == "ok", res.errors
    assert res.tool_calls[0] == "close_change"
    second = client.models.requests[1]["contents"]
    frs = [p.function_response for c in second for p in (c.parts or []) if p.function_response]
    assert frs and frs[-1].name == "close_change" and "error" in frs[-1].response
    results = evaluate(res.evidence, DeployRecord(**deploys["CHG-104390"]), directory)
    sod = [r for r in results if r.attribute == "independent_approver"][0]
    assert sod.result == "exception"
    assert overall(results) == "exception"


def test_function_response_follows_function_call(samples, tools, client_for):
    client = client_for("S01")
    extract(client, samples["S01"], tools)
    second = client.models.requests[1]["contents"]
    assert any(p.function_call and p.function_call.name == "get_ticket_approvals" for c in second for p in (c.parts or []))
    fr = [p.function_response for c in second for p in (c.parts or []) if p.function_response]
    assert fr and fr[0].name == "get_ticket_approvals"
    assert "lpatel" in json.dumps(fr[0].response)


def test_sample_goes_in_contents_not_system_instruction(samples, tools, client_for):
    client = client_for("S01")
    extract(client, samples["S01"], tools)
    req = client.models.requests[0]
    assert "CHG-104118" not in str(req["config"].system_instruction)
    first = " ".join(p.text or "" for c in req["contents"] for p in (c.parts or []))
    assert "CHG-104118" in first and "2231" in first
    assert req["model"] == "gemini-3.8-flash"


def test_exhausted_retries_go_to_review(samples, tools):
    bad = json.dumps(good(change_id="CHG-104118", tests_passed="maybe"))
    client = FakeClient([text_response("not json"), text_response(bad), text_response("{}"), text_response(json.dumps(GOOD))])
    res = extract(client, samples["S01"], tools)
    assert res.status == "needs_review" and res.evidence is None
    assert res.attempts == 3 and len(client.models.requests) == 3
    assert len(res.errors) >= 3


def test_wrong_change_id_is_not_accepted(samples, tools):
    other = json.dumps(good(change_id="CHG-999999"))
    client = FakeClient([text_response(other), text_response(json.dumps(GOOD))])
    res = extract(client, samples["S01"], tools)
    assert res.status == "ok" and res.attempts == 2
    assert res.evidence.change_id == "CHG-104118"


def test_tool_exception_goes_back_to_model(samples, tools):
    def boom(**kw):
        raise TimeoutError("change system timed out")
    t = dict(tools)
    t["get_ticket_approvals"] = boom
    client = FakeClient([call_response("get_ticket_approvals", {"change_id": "CHG-104118"}), text_response(json.dumps(GOOD))])
    res = extract(client, samples["S01"], t)
    assert res.status == "ok"
    fr = [p.function_response for c in client.models.requests[1]["contents"] for p in (c.parts or []) if p.function_response]
    assert "timed out" in json.dumps(fr[0].response)


def test_tool_budget_is_bounded(samples, tools):
    loop = [call_response("get_pr_checks", {"pr_number": 2231}) for _ in range(10)]
    client = FakeClient(loop)
    res = extract(client, samples["S01"], tools, max_tool_turns=4)
    assert res.status == "needs_review"
    assert len(client.models.requests) <= 5


def test_safety_stop_is_not_retried(samples, tools):
    client = FakeClient([text_response("", finish_reason="SAFETY"), text_response(json.dumps(GOOD))])
    res = extract(client, samples["S01"], tools)
    assert res.status == "needs_review"
    assert len(client.models.requests) == 1


# ---------------- attributes ----------------

def dep(**over):
    d = {"change_id": "CHG-104118", "pr_number": 2231, "environment": "prod",
         "deployed_at": "2026-03-04T16:20:00Z", "pipeline_run": "deploy-88120"}
    d.update(over)
    return DeployRecord(**d)


DIRECTORY = {"dkwan": "E1041", "lpatel": "E0877", "LPatel@meridianfreight.example": "E0877"}


def results_of(ev, deploy=None):
    return {r.attribute: r.result for r in evaluate(ChangeEvidence.model_validate(ev), deploy or dep(), DIRECTORY)}


def test_attribute_order():
    out = evaluate(ChangeEvidence.model_validate(GOOD), dep(), DIRECTORY)
    assert [r.attribute for r in out] == ["approval_before_deploy", "independent_approver", "linked_change", "tests_passed"]


def test_approval_at_same_instant_is_exception():
    assert results_of(good(approval_at="2026-03-04T10:20:00-06:00"))["approval_before_deploy"] == "exception"


def test_approval_one_minute_before_in_other_zone_passes():
    assert results_of(good(approval_at="2026-03-04T18:19:00+02:00"))["approval_before_deploy"] == "pass"


def test_no_approval_is_two_exceptions():
    r = results_of(good(approver=None, approval_at=None))
    assert r["approval_before_deploy"] == "exception" and r["independent_approver"] == "exception"


def test_unknown_identity_needs_review():
    ev = good(approver="contractor99")
    r = results_of(ev)
    assert r["independent_approver"] == "not_evaluable"
    assert overall(evaluate(ChangeEvidence.model_validate(ev), dep(), DIRECTORY)) == "needs_review"


def test_email_alias_is_same_person():
    assert results_of(good(author="lpatel", approver="lpatel@MeridianFreight.example"))["independent_approver"] == "exception"


def test_tests_failed_and_unknown():
    assert results_of(good(tests_passed=False))["tests_passed"] == "exception"
    assert results_of(good(tests_passed=None))["tests_passed"] == "not_evaluable"


def test_linked_change_mismatch():
    assert results_of(GOOD, dep(pr_number=2232))["linked_change"] == "exception"
    assert results_of(GOOD, dep(change_id="CHG-104119"))["linked_change"] == "exception"
