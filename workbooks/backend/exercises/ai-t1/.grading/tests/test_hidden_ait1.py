import pathlib
import re

from assistant_tools import audit
from assistant_tools.replay import replay
from assistant_tools.tools import TOOLS, call_tool
from testkit import leaked


def test_replay_no_cross_tenant_rows_and_the_injected_call_fails():
    results = replay("transcripts/inc-7731.json")
    assert leaked(results, "bu-amer") == []
    assert results[2]["result"]["is_error"] is True
    assert results[1]["result"]["is_error"] is False


def test_schemas_expose_no_tenant_and_are_closed():
    for name, t in TOOLS.items():
        props = t["input_schema"].get("properties", {})
        assert not any("tenant" in p for p in props), name
        assert t["input_schema"].get("additionalProperties") is False, name


def test_tenant_argument_is_rejected_and_audited(amer):
    r = call_tool(amer, "get_account_timeline", {"account_id": "acc-amer-0001", "tenant_id": "bu-amer"})
    assert r["is_error"] is True
    assert audit.AUDIT and audit.AUDIT[-1]["outcome"] == "denied"


def test_other_tenants_account_is_not_found(amer, emea):
    r = call_tool(amer, "get_account_timeline", {"account_id": "acc-emea-0007"})
    assert r["is_error"] is True and "not found" in str(r["content"]).lower()
    assert "Fjordline" not in str(r["content"])
    ok = call_tool(emea, "get_account_timeline", {"account_id": "acc-emea-0007"})
    assert ok["is_error"] is False and ok["content"]["account"]["name"] == "Fjordline Shipping"
    assert audit.AUDIT[-2]["outcome"] in ("denied", "not_found")


def test_every_call_is_fully_audited(amer):
    calls = [("find_account", {"query": "bright"}), ("get_account_timeline", {"account_id": "acc-amer-0001"}),
             ("get_account_timeline", {"account_id": "acc-emea-0008"}), ("get_account_timeline", {"account_id": "x", "tenant_id": "bu-emea"})]
    for name, args in calls:
        call_tool(amer, name, dict(args))
    assert len(audit.AUDIT) == len(calls)
    for entry, (name, args) in zip(audit.AUDIT, calls):
        for k in ("ts", "trace_id", "agent_id", "on_behalf_of", "tenant_id", "tool", "args_sha256", "outcome"):
            assert k in entry, k
        assert entry["agent_id"] == "sales-assistant" and entry["on_behalf_of"] == "u-jlee"
        assert entry["tenant_id"] == "bu-amer" and entry["tool"] == name and entry["trace_id"] == "t-amer-1"
        assert entry["args_sha256"] == audit.args_sha256(args)
    assert [e["outcome"] for e in audit.AUDIT][:2] == ["ok", "ok"]


def test_timeline_items_are_marked_untrusted(amer):
    r = call_tool(amer, "get_account_timeline", {"account_id": "acc-amer-0001"})
    assert not r["is_error"] and len(r["content"]["activities"]) == 2
    assert all(item.get("untrusted") is True for item in r["content"]["activities"])


def test_limit_is_bounded(amer):
    r = call_tool(amer, "get_account_timeline", {"account_id": "acc-amer-0001", "limit": 500})
    assert r["is_error"] is True
    ok = call_tool(amer, "get_account_timeline", {"account_id": "acc-amer-0001", "limit": 1})
    assert len(ok["content"]["activities"]) == 1


def test_answer_names_argument_derived_authorization():
    text = pathlib.Path("ANSWER.md").read_text().lower()
    assert re.search(r"confused deputy|tenant_id (argument|parameter)|tenant from (the )?(tool )?argument|model-(supplied|controlled)", text)
