"""Hidden tests for audit/ai-c1: scoping, pagination, actionable errors, tool metadata, gated write."""

from __future__ import annotations

import base64
import json

import pytest

from grcmcp.tokens import ApprovalError, issue_approval, verify_approval

ENG = "ENG-2026-SOX-ITGC"
KEY = b"test-review-service-key-0f3a"
NOW = 1_793_000_000.0
DESC = "approval recorded after the production deploy"


def tok(**over):
    kw = dict(engagement=ENG, control_id="CM-03", sample_id="CHG-104117", reviewer="kbrooks", expires_at=int(NOW) + 3600)
    kw.update(over)
    return issue_approval(KEY, **kw)


def rec_args(**over):
    a = {"control_id": "CM-03", "sample_id": "CHG-104117", "description": DESC, "approval_token": tok()}
    a.update(over)
    return a


# ---------- tool metadata ----------

def test_tool_set_and_annotations(mcp):
    tools = {t.name: t for t in mcp.tools()}
    assert set(tools) == {"list_controls", "get_control_test", "search_exceptions", "get_evidence_index", "record_exception"}
    for name in ("list_controls", "get_control_test", "search_exceptions", "get_evidence_index"):
        assert tools[name].annotations and tools[name].annotations.read_only_hint is True, name
    assert tools["record_exception"].annotations and tools["record_exception"].annotations.read_only_hint is False


def test_descriptions_are_written_for_a_model(mcp):
    tools = {t.name: t for t in mcp.tools()}
    for t in tools.values():
        assert t.description and len(t.description) >= 60, t.name
    assert "approval" in tools["record_exception"].description.lower()
    assert "cursor" in tools["search_exceptions"].description.lower()
    props = tools["search_exceptions"].input_schema["properties"]
    assert props["limit"]["type"] == "integer"
    assert set(tools["record_exception"].input_schema["required"]) == {"control_id", "sample_id", "description", "approval_token"}


# ---------- scoping ----------

def test_control_test_is_this_engagement(mcp):
    err, data, _ = mcp.call("get_control_test", {"control_id": "CM-03"})
    assert not err and data["sample_size"] == 25


def test_other_engagement_control_is_not_found_with_guidance(mcp):
    err, _, text = mcp.call("get_control_test", {"control_id": "TR-09"})
    assert err
    assert "TR-09" in text and "CM-03" in text and "list_controls" in text


def test_search_only_returns_this_engagement(mcp):
    err, data, _ = mcp.call("search_exceptions", {"limit": 50})
    assert not err
    assert data["total"] == 23 and all(e["exception_id"].startswith("EXC-") for e in data["items"])


def test_evidence_index_scoped(mcp):
    err, data, _ = mcp.call("get_evidence_index", {"control_id": "CM-03", "sample_id": "CHG-104117"})
    assert not err and [d["doc_id"] for d in data["documents"]] == ["EV-0411", "EV-0412", "EV-0413"]
    err, data, _ = mcp.call("get_evidence_index", {"control_id": "CM-03", "sample_id": "CHG-104134"})
    assert not err and data["documents"] == []
    err, _, text = mcp.call("get_evidence_index", {"control_id": "CM-03", "sample_id": "CHG-999999"})
    assert err and "CHG-999999" in text


# ---------- pagination ----------

def test_pagination_walks_every_result_once(mcp):
    seen, cursor, pages = [], None, 0
    while True:
        args = {"status": "open", "limit": 4}
        if cursor:
            args["cursor"] = cursor
        err, data, text = mcp.call("search_exceptions", args)
        assert not err, text
        seen += [e["exception_id"] for e in data["items"]]
        pages += 1
        cursor = data["next_cursor"]
        if not cursor:
            break
        assert pages < 10
    assert len(seen) == len(set(seen)) == 11 and seen == sorted(seen) and pages == 3


def test_query_filters(mcp):
    err, data, _ = mcp.call("search_exceptions", {"query": "SELF-APPROVAL", "limit": 50})
    assert not err and data["total"] >= 1
    assert all("self-approval" in e["description"] for e in data["items"])


@pytest.mark.parametrize("args,word", [
    ({"limit": 0}, "limit"), ({"limit": 51}, "limit"), ({"status": "pending"}, "status"), ({"cursor": "%%%notacursor"}, "cursor"),
], ids=["limit-0", "limit-51", "bad-status", "garbage-cursor"])
def test_search_errors_are_actionable(mcp, args, word):
    err, _, text = mcp.call("search_exceptions", args)
    assert err and word in text.lower()


def test_cursor_from_other_query_is_rejected(mcp):
    _, data, _ = mcp.call("search_exceptions", {"status": "open", "limit": 2})
    err, _, text = mcp.call("search_exceptions", {"status": "closed", "limit": 2, "cursor": data["next_cursor"]})
    assert err and "cursor" in text.lower()


# ---------- tokens ----------

def test_token_format_and_roundtrip():
    t = tok()
    b64, sig = t.split(".")
    payload = json.loads(base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4)))
    assert payload == {"eng": ENG, "control": "CM-03", "sample": "CHG-104117", "reviewer": "kbrooks", "exp": int(NOW) + 3600}
    assert len(sig) == 64
    a = verify_approval(KEY, t, engagement=ENG, control_id="CM-03", sample_id="CHG-104117", now=NOW)
    assert a.reviewer == "kbrooks"


def test_token_errors():
    with pytest.raises(ApprovalError, match="signature"):
        verify_approval(b"other-key", tok(), engagement=ENG, control_id="CM-03", sample_id="CHG-104117", now=NOW)
    with pytest.raises(ApprovalError, match="expired"):
        verify_approval(KEY, tok(expires_at=int(NOW) - 1), engagement=ENG, control_id="CM-03", sample_id="CHG-104117", now=NOW)
    with pytest.raises(ApprovalError, match="scope"):
        verify_approval(KEY, tok(sample_id="CHG-104134"), engagement=ENG, control_id="CM-03", sample_id="CHG-104117", now=NOW)
    with pytest.raises(ApprovalError, match="malformed"):
        verify_approval(KEY, "not-a-token", engagement=ENG, control_id="CM-03", sample_id="CHG-104117", now=NOW)


# ---------- gated write ----------

def _tampered():
    b64, sig = tok().split(".")
    payload = json.loads(base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4)))
    payload["sample"] = "CHG-104134"
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(body).decode().rstrip("=") + "." + sig


@pytest.mark.parametrize("make,word", [
    (lambda: {"approval_token": "forged.token"}, "malformed"),
    (lambda: {"approval_token": _tampered(), "sample_id": "CHG-104134"}, "signature"),
    (lambda: {"approval_token": tok(expires_at=int(NOW) - 60)}, "expired"),
    (lambda: {"approval_token": tok(sample_id="CHG-104134")}, "scope"),
    (lambda: {"approval_token": tok(engagement="ENG-2026-SOC1-RATES")}, "scope"),
    (lambda: {"approval_token": tok(reviewer="RAlvarez")}, "preparer"),
    (lambda: {"description": "bad"}, "description"),
], ids=["forged", "tampered", "expired", "other-sample", "other-engagement", "preparer-approves", "short-description"])
def test_record_exception_rejections(mcp, store, make, word):
    err, _, text = mcp.call("record_exception", rec_args(**make()))
    assert err and word in text.lower(), text
    assert store.writes == []


def test_recorded_exception_is_searchable_and_not_duplicated(mcp, store):
    err, data, text = mcp.call("record_exception", rec_args())
    assert not err, text
    err2, _, text2 = mcp.call("record_exception", rec_args())
    assert err2 and "already" in text2.lower()
    assert len(store.writes) == 1
    _, found, _ = mcp.call("search_exceptions", {"query": "CHG-104117", "status": "open"})
    assert data["exception_id"] in [e["exception_id"] for e in found["items"]]
    w = store.writes[0]
    assert w["approved_by"] == "kbrooks" and w["raised_by"] == "ralvarez" and w["engagement"] == ENG
