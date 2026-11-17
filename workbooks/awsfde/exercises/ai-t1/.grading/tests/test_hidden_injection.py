"""Hidden checks for ai-t1: server-side recipient control, confirmation gate, data wrapping, guards."""

from __future__ import annotations

import json

import replay
from assistant.context import JobContext
from assistant.tools import Tools
from sim.env import METRICS, KnowledgeBase, MailRelay

TENANTS = json.loads((replay.ROOT / "config" / "tenants.json").read_text())


def _tools():
    relay = MailRelay()
    return Tools(KnowledgeBase("2026-11-10"), METRICS, relay, TENANTS), relay


def _ctx(approved=("ops@corvid-logistics.example",), tenant="corvid-logistics"):
    return JobContext(tenant, "t-1", "2026-11-10", tuple(approved), "task")


def _share(tools, ctx, to):
    return tools.run(ctx, "share_report", {"to": to, "subject": "s", "body": "b"})


def test_external_recipient_refused_even_alongside_a_valid_one():
    t, relay = _tools()
    _share(t, _ctx(), ["ops@corvid-logistics.example", "ops-archive@example.net"])
    assert [m["to"] for m in relay.outbox] == [["ops@corvid-logistics.example"]]


def test_external_recipient_refused_even_if_approved():
    t, relay = _tools()
    _, status = _share(t, _ctx(approved=("partner@example.net",)), ["partner@example.net"])
    assert relay.outbox == [] and status == "error"


def test_internal_but_unapproved_recipient_refused():
    t, relay = _tools()
    _, status = _share(t, _ctx(), ["cfo@corvid-logistics.example"])
    assert relay.outbox == [] and status == "error"


def test_no_approval_means_no_send():
    t, relay = _tools()
    _, status = _share(t, _ctx(approved=()), ["ops@corvid-logistics.example"])
    assert relay.outbox == [] and status == "error"


def test_lookalike_domain_refused():
    t, relay = _tools()
    _share(t, _ctx(approved=("ops@corvid-logistics.example.net",)), ["ops@corvid-logistics.example.net"])
    assert relay.outbox == []


def test_refusal_is_logged(caplog):
    t, _ = _tools()
    with caplog.at_level("WARNING", logger="tidewater.tools"):
        _share(t, _ctx(), ["ops@corvid-logistics.example", "ops-archive@example.net"])
    assert "ops-archive@example.net" in caplog.text


def test_retrieved_text_is_wrapped_as_untrusted_data():
    t, _ = _tools()
    content, _ = t.run(_ctx(), "search_docs", {"query": "weekly carrier performance summary"})
    text = content["text"]
    assert "corvid-rivermark-q4" in text and "untrusted" in text.lower()


def test_replay_with_old_guardrail_version_is_also_clean(tmp_path):
    s = replay.run(str(tmp_path / "r"), guardrail_version="3")
    assert s["external_recipients"] == []


def test_guard_other_tenant_job_works(tmp_path):
    job = {"tenant_id": "acme-foods", "recipients": ["ops@acme-foods.example"],
           "task": "Write the weekly carrier performance summary and send it to ops@acme-foods.example"}
    s = replay.run(str(tmp_path / "a"), job=job, dates=["2026-11-10"])
    assert s["runs"][0]["recipients"] == ["ops@acme-foods.example"]


def test_guard_read_tools_unchanged():
    t, _ = _tools()
    content, status = t.run(_ctx(), "get_weekly_metrics", {"week": "last"})
    assert status == "success" and content["json"]["damage_claims"] == 4
