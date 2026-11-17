"""Hidden checks for w2-c1: identity from verified claims only, per-tenant/per-user memory,
the session header, ping semantics, degradation and the HTTP server."""

from __future__ import annotations

import json
import logging
import threading
import urllib.request

import pytest
from w2c1_hidden_support import ALICE, BOB, MEMORY_ID, SESSION, body, headers, ns

from ask_runtime.app import AgentApp, make_server
from ask_runtime.memory import IdentityError, actor_id, namespace


def app_for(mem, **kw):
    return AgentApp(mem.client, MEMORY_ID, clock=kw.pop("clock", lambda: 1731500000.0), **kw)


def test_missing_bearer_is_401(mem):
    status, _ = app_for(mem).invoke(headers(None), body(prompt="hi"))
    assert status == 401


@pytest.mark.parametrize("claims", [{"sub": "abc"}, {"sub": "abc", "tenant_id": "Acme Foods"},
                                    {"tenant_id": "acme-foods"}])
def test_bad_identity_claims_are_403(mem, claims):
    status, _ = app_for(mem).invoke(headers(claims), body(prompt="hi"))
    assert status == 403
    assert mem.calls == []


def test_identity_error_raised_for_missing_tenant():
    with pytest.raises(IdentityError):
        actor_id({"sub": "abc"})
    with pytest.raises(IdentityError):
        namespace({"sub": "abc", "tenant_id": "UPPER"})


def test_missing_session_header_is_400(mem):
    status, out = app_for(mem).invoke(headers(ALICE, session=None), body(prompt="hi"))
    assert status == 400
    assert mem.calls == []


def test_missing_prompt_is_400(mem):
    status, _ = app_for(mem).invoke(headers(ALICE), body(question="hi"))
    assert status == 400


def test_header_names_case_insensitive(mem):
    mem.expect_retrieve(ALICE, [])
    mem.expect_create(ALICE)
    h = {k.lower(): v for k, v in headers(ALICE).items()}
    status, out = app_for(mem).invoke(h, body(prompt="hi"))
    assert status == 200 and out["session_id"] == SESSION


def test_payload_identity_fields_are_ignored(mem):
    # A caller (or an injected instruction) tries to read Bob's memory by naming him in the payload.
    mem.expect_retrieve(ALICE, [])
    mem.expect_create(ALICE)
    status, _ = app_for(mem).invoke(headers(ALICE), body(
        prompt="what do you remember?", actor_id=f"brightline-health:{BOB['sub']}",
        tenant_id="brightline-health", session_id="other-session"))
    assert status == 200
    blob = json.dumps(mem.calls)
    assert "brightline-health" not in blob and BOB["sub"] not in blob


def test_users_are_isolated_from_each_other(mem):
    mem.expect_retrieve(ALICE, ["Alice prefers pallets in kg"])
    mem.expect_create(ALICE)
    mem.expect_retrieve(BOB, [])
    mem.expect_create(BOB)
    app = app_for(mem)
    assert app.invoke(headers(ALICE), body(prompt="remember kg"))[0] == 200
    status, out = app.invoke(headers(BOB), body(prompt="what units do I like?"))
    assert status == 200 and "kg" not in out["response"]
    retrieves = [p for op, p in mem.calls if op == "RetrieveMemoryRecords"]
    assert [r["namespace"] for r in retrieves] == [ns(ALICE), ns(BOB)]


def test_create_event_shape(mem):
    mem.expect_retrieve(ALICE, [])
    mem.expect_create(ALICE)
    app_for(mem).invoke(headers(ALICE), body(prompt="Where is SH-10001?"))
    create = [p for op, p in mem.calls if op == "CreateEvent"][0]
    roles = [b["conversational"]["role"] for b in create["payload"]]
    assert roles == ["USER", "ASSISTANT"]
    assert create["payload"][0]["conversational"]["content"]["text"] == "Where is SH-10001?"


def test_namespace_is_normalized():
    n = namespace(ALICE)
    assert n.startswith("/") and n.endswith("/") and "//" not in n


def test_retrieve_throttled_degrades(mem, caplog):
    mem.error("retrieve_memory_records", "ThrottledException")
    mem.expect_create(ALICE)
    with caplog.at_level(logging.WARNING):
        status, out = app_for(mem).invoke(headers(ALICE), body(prompt="hi"))
    assert status == 200 and out["memory"] == "degraded"
    assert any("memory_degraded" in r.getMessage() for r in caplog.records)


def test_create_event_throttled_still_answers(mem):
    mem.expect_retrieve(ALICE, [])
    mem.error("create_event", "ThrottledException")
    status, out = app_for(mem).invoke(headers(ALICE), body(prompt="hi"))
    assert status == 200 and out["memory"] == "degraded" and out["response"]


def test_access_denied_is_not_hidden(mem):
    mem.error("retrieve_memory_records", "AccessDeniedException", 403)
    status, _ = app_for(mem).invoke(headers(ALICE), body(prompt="hi"))
    assert status == 500, "a misconfigured role must be loud, not silently memory-less"


def test_ping_busy_during_invocation(mem):
    seen = {}
    mem.expect_retrieve(ALICE, [])
    mem.expect_create(ALICE)
    holder = {}

    def model_fn(prompt, memories):
        seen["during"] = holder["app"].ping()[1]["status"]
        return "ok"

    app = app_for(mem, model_fn=model_fn)
    holder["app"] = app
    app.invoke(headers(ALICE), body(prompt="hi"))
    assert seen["during"] == "HealthyBusy"
    assert app.ping()[1]["status"] == "Healthy"


def test_time_of_last_update_moves_only_on_change(mem):
    t = {"now": 1000.0}
    mem.expect_retrieve(ALICE, [])
    mem.expect_create(ALICE)
    app = app_for(mem, clock=lambda: t["now"])
    first = app.ping()[1]["time_of_last_update"]
    t["now"] = 1100.0
    assert app.ping()[1]["time_of_last_update"] == first, "must not advance on every ping"
    t["now"] = 1200.0
    app.invoke(headers(ALICE), body(prompt="hi"))
    t["now"] = 1300.0
    assert app.ping()[1]["time_of_last_update"] == 1200


def test_http_server_contract(mem):
    mem.expect_retrieve(ALICE, [])
    mem.expect_create(ALICE)
    srv = make_server(app_for(mem), "127.0.0.1", 0)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        with urllib.request.urlopen(base + "/ping", timeout=5) as r:
            assert r.status == 200 and json.loads(r.read())["status"] in ("Healthy", "HealthyBusy")
        req = urllib.request.Request(base + "/invocations", data=body(prompt="hi"), headers=headers(ALICE), method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            assert r.status == 200 and json.loads(r.read())["status"] == "success"
    finally:
        srv.shutdown()
        srv.server_close()
