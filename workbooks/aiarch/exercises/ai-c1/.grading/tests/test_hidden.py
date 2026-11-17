import pytest

from changemgmt.backends import ChangeStore, Cmdb
from changemgmt.server import build_server
from mcputil import call, session, tools

GOOD = {"service": "claims-intake", "summary": "Rotate TLS certificate on the intake ALB", "risk": "low",
        "window_start": "2026-11-20T02:00:00Z"}


def test_invalid_token_builds_no_server():
    with pytest.raises(Exception):
        build_server(ChangeStore(), Cmdb(), "tok-forged")


def test_read_tools_annotated_read_only():
    ts = {t.name: t for t in tools(session()[0])}
    for n in ("get_change", "list_my_open_changes"):
        assert ts[n].annotations and ts[n].annotations.read_only_hint is True
    for n in ("create_change", "add_comment"):
        assert not (ts[n].annotations and ts[n].annotations.read_only_hint)


def test_descriptions_written_for_the_model():
    for t in tools(session()[0]):
        assert t.description and len(t.description) >= 30, t.name


@pytest.mark.parametrize("bad", [{"risk": "critical"}, {"summary": "short"}, {"window_start": "next tuesday"},
                                 {"summary": "x" * 201}])
def test_create_validation(bad):
    srv, store = session()
    n = len(store.changes)
    err, _ = call(srv, "create_change", {**GOOD, **bad})
    assert err and len(store.changes) == n


def test_retired_service_rejected():
    srv, _ = session()
    err, body = call(srv, "create_change", {**GOOD, "service": "fax-gateway"})
    assert err and "retired" in str(body)


def test_high_risk_needs_lead_time():
    srv, _ = session()
    err, body = call(srv, "create_change", {**GOOD, "risk": "high", "window_start": "2026-11-16T02:00:00Z"})
    assert err and "48" in str(body)


def test_create_output_is_small():
    srv, _ = session("mchen")
    err, body = call(srv, "create_change", {**GOOD, "service": "agent-gateway"})
    assert not err and set(body) <= {"change_id", "state", "approver_group"} and body["approver_group"] == "platform-engineering"


def test_get_change_validation_and_not_found():
    srv, store = session()
    err, _ = call(srv, "get_change", {"change_id": "10002"})
    assert err and store.calls == [], "invalid ids must be rejected before calling the backend"
    err, body = call(srv, "get_change", {"change_id": "CHG-99999"})
    assert err and "list_my_open_changes" in str(body)


def test_get_change_trimmed():
    err, body = call(session()[0], "get_change", {"change_id": "CHG-10001"})
    assert not err and "comments" not in body and body["comment_count"] == 1


def test_list_open_only_and_paginated():
    srv, _ = session("lwong")
    seen, cursor, pages = [], None, 0
    while True:
        args = {"cursor": cursor} if cursor else {}
        err, body = call(srv, "list_my_open_changes", args)
        assert not err and len(body["changes"]) <= 5
        seen += [c["change_id"] for c in body["changes"]]
        pages += 1
        cursor = body.get("next_cursor")
        if not cursor:
            break
    assert pages == 2 and len(seen) == 10 and "CHG-10003" not in seen and "CHG-10004" not in seen


def test_list_is_per_caller():
    err, body = call(session("mchen")[0], "list_my_open_changes", {})
    assert [c["change_id"] for c in body["changes"]] == ["CHG-10004"]


def test_bad_cursor_is_actionable():
    err, body = call(session()[0], "list_my_open_changes", {"cursor": "garbage!!"})
    assert err and "cursor" in str(body)


def test_comment_permissions():
    srv, store = session("pnair")
    err, _ = call(srv, "add_comment", {"change_id": "CHG-10004", "text": "Gateway owners approve"})
    assert not err
    err, body = call(srv, "add_comment", {"change_id": "CHG-10002", "text": "drive-by"})
    assert err and "payments-sre" in str(body)
    assert len(store.changes["CHG-10002"]["comments"]) == 0


def test_comment_length_cap():
    err, _ = call(session()[0], "add_comment", {"change_id": "CHG-10002", "text": "x" * 2001})
    assert err
