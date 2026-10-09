"""Visible tests: the fixed state, checked in-process against gateway.env (not against
the processes make setup started). The grader adds hidden tests."""

from __future__ import annotations

from w2t1_support import call, gateway


async def test_tokens_signed_with_the_current_key_are_accepted(idp, clock):
    async with gateway(idp, clock) as (client, _):
        response = await call(client, idp.token("k-2026-09"))
    assert response.status_code == 200
    assert response.json()["result"]["principal"] == "cust-1001"


async def test_new_kid_is_accepted_after_a_rotation_without_a_restart(idp, clock):
    async with gateway(idp, clock) as (client, _):
        clock.t += 3600  # an hour after the gateway started, the IdP rotates
        idp.add("k-2026-10")
        response = await call(client, idp.token("k-2026-10"))
    assert response.status_code == 200, "new-kid tokens must verify without restarting the gateway"
