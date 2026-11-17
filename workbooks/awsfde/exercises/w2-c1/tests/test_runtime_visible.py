"""Visible checks for w2-c1 (happy paths). The grader runs more."""

from __future__ import annotations

from w2c1_support import ALICE, MEMORY_ID, body, headers

from ask_runtime.app import AgentApp
from ask_runtime.memory import actor_id, namespace


def test_actor_and_namespace_from_claims():
    assert actor_id(ALICE) == "acme-foods:7f3a9c2e-0b1d-4c55-9e0a-2a1b3c4d5e6f"
    assert namespace(ALICE) == "/tenant/acme-foods/actor/acme-foods:7f3a9c2e-0b1d-4c55-9e0a-2a1b3c4d5e6f/preferences/"


def test_ping_idle():
    app = AgentApp(None, MEMORY_ID, clock=lambda: 1731500000.0)
    status, payload = app.ping()
    assert status == 200 and payload["status"] == "Healthy"


def test_invocation_recalls_and_remembers(mem):
    mem.expect_retrieve(ALICE, ["Prefers metric units", "Main DC is Fresno"])
    mem.expect_create(ALICE)
    app = AgentApp(mem.client, MEMORY_ID, clock=lambda: 1731500000.0)
    status, out = app.invoke(headers(ALICE), body(prompt="Where is SH-10001?"))
    assert status == 200, out
    assert out["status"] == "success" and "Prefers metric units" in out["response"]
    mem.stub.assert_no_pending_responses()
