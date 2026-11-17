"""Visible tests: the happy path, the unauthenticated challenge, the metadata document and
one expired token. The grader adds hidden tests for the rest of the README criteria."""

from __future__ import annotations

import time

import pytest
from w2c1_support import SETTINGS, make_verifier, mcp_session, running_app

from mcp_auth.verifier import InvalidToken


async def test_valid_token_round_trips_through_mcp_and_sub_is_the_identity(idp):
    async with running_app(idp) as client:
        async with mcp_session(client, idp.token("k-2026-09", sub="cust-1001")) as session:
            result = await session.call_tool("whoami", {})
            assert not result.isError
            assert result.content[0].text == "cust-1001"


async def test_missing_token_gets_401_with_resource_metadata_challenge(idp):
    async with running_app(idp) as client:
        response = await client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
    assert response.status_code == 401
    challenge = response.headers["www-authenticate"]
    assert challenge.startswith("Bearer ")
    assert f'resource_metadata="{SETTINGS.resource_metadata_url}"' in challenge


async def test_protected_resource_metadata_is_public(idp):
    async with running_app(idp) as client:
        response = await client.get("/.well-known/oauth-protected-resource")
    assert response.status_code == 200
    doc = response.json()
    assert doc["resource"] == SETTINGS.resource
    assert doc["authorization_servers"] == [SETTINGS.issuer]


async def test_expired_token_is_rejected(idp):
    verifier, _ = make_verifier(idp)
    now = int(time.time())
    token = idp.token("k-2026-09", iat=now - 3600, nbf=now - 3600, exp=now - 600)
    with pytest.raises(InvalidToken):
        await verifier.verify(token)
