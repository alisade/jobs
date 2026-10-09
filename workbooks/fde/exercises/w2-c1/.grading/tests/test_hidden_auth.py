"""Hidden tests for fde/w2-c1: claims, algorithm pinning, JWKS rotation and caching,
scopes, and per-principal identity."""

from __future__ import annotations

import asyncio
import base64
import json
import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from w2c1_hidden_support import (
    BASE,
    MCP_HEADERS,
    SETTINGS,
    b64url,
    ec_key,
    make_verifier,
    mcp_call,
    mcp_session,
    rsa_key,
    running_app,
)

from mcp_auth.verifier import InvalidToken

KID = "k-2026-09"


class Clock:
    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t


async def _rejects(verifier, token):
    with pytest.raises(InvalidToken):
        await verifier.verify(token)


# -- claims -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "https://other-service.example/mcp"},
        {"iss": "https://evil.example/"},
        {"nbf": int(time.time()) + 600},
    ],
    ids=["wrong-aud", "wrong-iss", "nbf-future"],
)
async def test_bad_claims_are_rejected(idp, overrides):
    verifier, _ = make_verifier(idp)
    await _rejects(verifier, idp.token(KID, **overrides))


@pytest.mark.parametrize("claim", ["exp", "sub", "iat"])
async def test_required_claims_are_enforced(idp, claim):
    verifier, _ = make_verifier(idp)
    await _rejects(verifier, idp.token(KID, drop=(claim,)))


async def test_small_clock_skew_is_tolerated(idp):
    verifier, _ = make_verifier(idp)
    now = int(time.time())
    token = idp.token(KID, iat=now - 300, nbf=now - 300, exp=now - 10)  # 10s < 30s leeway
    principal = await verifier.verify(token)
    assert principal.sub == "cust-1001"
    assert principal.scopes == frozenset({"cart:read", "cart:write"})


# -- algorithm pinning ------------------------------------------------------------------------


async def test_alg_none_is_rejected(idp):
    verifier, _ = make_verifier(idp)
    now = int(time.time())
    header = b64url(json.dumps({"alg": "none", "kid": KID, "typ": "JWT"}).encode())
    body = b64url(json.dumps({"iss": SETTINGS.issuer, "aud": SETTINGS.resource, "sub": "x",
                              "iat": now, "exp": now + 300}).encode())
    await _rejects(verifier, f"{header}.{body}.")


async def test_hs256_with_the_public_key_as_secret_is_rejected(idp):
    verifier, _ = make_verifier(idp)
    pem = idp.keys[KID].private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    now = int(time.time())
    claims = {"iss": SETTINGS.issuer, "aud": SETTINGS.resource, "sub": "attacker",
              "iat": now, "exp": now + 300}
    signing_input = (
        b64url(json.dumps({"alg": "HS256", "kid": KID, "typ": "JWT"}).encode())
        + "."
        + b64url(json.dumps(claims).encode())
    )
    import hashlib
    import hmac

    sig = hmac.new(pem, signing_input.encode(), hashlib.sha256).digest()
    await _rejects(verifier, signing_input + "." + base64.urlsafe_b64encode(sig).rstrip(b"=").decode())


async def test_alg_outside_the_allow_list_is_rejected(idp):
    verifier, _ = make_verifier(idp)
    now = int(time.time())
    token = jwt.encode(
        {"iss": SETTINGS.issuer, "aud": SETTINGS.resource, "sub": "x", "iat": now, "exp": now + 300},
        idp.keys[KID].private, algorithm="RS384", headers={"kid": KID},
    )
    await _rejects(verifier, token)


async def test_es256_keys_work_and_alg_must_match_the_key_type(idp):
    idp.add(ec_key("ec-1"))
    verifier, _ = make_verifier(idp)
    assert (await verifier.verify(idp.token("ec-1", sub="cust-ec"))).sub == "cust-ec"
    # An RS256 token whose header points at the EC key's kid.
    now = int(time.time())
    forged = jwt.encode(
        {"iss": SETTINGS.issuer, "aud": SETTINGS.resource, "sub": "x", "iat": now, "exp": now + 300},
        idp.keys[KID].private, algorithm="RS256", headers={"kid": "ec-1"},
    )
    await _rejects(verifier, forged)


# -- JWKS cache ---------------------------------------------------------------------------------


async def test_rotation_new_kid_verifies_without_restart(idp):
    verifier, cache = make_verifier(idp)
    await verifier.verify(idp.token(KID))
    idp.add(rsa_key("k-2026-10"))  # the IdP publishes and starts signing with a new key
    assert (await verifier.verify(idp.token("k-2026-10", sub="cust-new"))).sub == "cust-new"
    assert (await verifier.verify(idp.token(KID))).sub == "cust-1001"  # overlap window
    assert cache.fetch_count == 2


async def test_unknown_kids_cannot_stampede_the_jwks_endpoint(idp):
    clock = Clock()
    verifier, cache = make_verifier(idp, clock=clock)
    await verifier.verify(idp.token(KID))
    for i in range(25):
        idp.add(rsa_key(f"junk-{i}"), publish=False)
        await _rejects(verifier, idp.token(f"junk-{i}"))
        clock.t += 0.5
    assert idp.fetches <= 2, f"{idp.fetches} JWKS fetches for 25 unknown kids"


async def test_refresh_allowed_again_after_the_cooldown(idp):
    clock = Clock()
    verifier, _ = make_verifier(idp, clock=clock)
    await verifier.verify(idp.token(KID))
    await _rejects(verifier, _unknown(idp))  # spends this window's unknown-kid refresh
    fetches = idp.fetches
    idp.add(rsa_key("k-late"))
    clock.t += 5  # inside the 30s cooldown: no refresh yet
    await _rejects(verifier, idp.token("k-late"))
    clock.t += SETTINGS.refresh_cooldown_s + 1
    assert (await verifier.verify(idp.token("k-late"))).sub == "cust-1001"
    assert idp.fetches == fetches + 1


def _unknown(idp):
    idp.add(rsa_key("never-published"), publish=False)
    return idp.token("never-published")


async def test_removed_key_stops_working_after_the_ttl(idp):
    clock = Clock()
    verifier, _ = make_verifier(idp, clock=clock)
    token = idp.token(KID)
    await verifier.verify(token)
    idp.add(rsa_key("k-next"))
    idp.published.remove(KID)  # revoked at the IdP
    clock.t += SETTINGS.cache_ttl_s + 1
    await _rejects(verifier, token)


async def test_jwks_outage_keeps_last_good_keys_and_cold_outage_is_a_401(idp):
    clock = Clock()
    verifier, _ = make_verifier(idp, clock=clock)
    await verifier.verify(idp.token(KID))
    idp.fail = True
    clock.t += SETTINGS.cache_ttl_s + 1
    assert (await verifier.verify(idp.token(KID))).sub == "cust-1001"
    cold, _ = make_verifier(idp)
    await _rejects(cold, idp.token(KID))  # InvalidToken, not an unhandled error


async def test_concurrent_cold_verifications_share_one_fetch(idp):
    verifier, cache = make_verifier(idp)
    tokens = [idp.token(KID, sub=f"c{i}") for i in range(12)]
    results = await asyncio.gather(*(verifier.verify(t) for t in tokens))
    assert [p.sub for p in results] == [f"c{i}" for i in range(12)]
    assert idp.fetches == 1


# -- HTTP surface -------------------------------------------------------------------------------


async def test_invalid_token_challenge_names_the_error_but_not_the_reason(idp):
    async with running_app(idp) as client:
        response = await client.post(
            "/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            headers={**MCP_HEADERS, "authorization": "Bearer " + idp.token(KID, aud="https://x/")},
        )
    assert response.status_code == 401
    challenge = response.headers["www-authenticate"]
    assert 'error="invalid_token"' in challenge and "resource_metadata=" in challenge
    assert "aud" not in response.text.lower() and "audience" not in response.text.lower()


async def test_write_tool_without_scope_is_403_insufficient_scope(idp):
    read_only = idp.token(KID, scope="cart:read")
    async with running_app(idp) as client:
        headers = {**MCP_HEADERS, "authorization": f"Bearer {read_only}"}
        denied = await client.post("/mcp", json=mcp_call("add_to_cart", {"product_id": "AR-1301"}),
                                   headers=headers)
        assert denied.status_code == 403
        challenge = denied.headers["www-authenticate"]
        assert 'error="insufficient_scope"' in challenge and 'scope="cart:write"' in challenge
        batch = [mcp_call("search_products", {"query": "mat"}, 1),
                 mcp_call("add_to_cart", {"product_id": "AR-1301"}, 2)]
        assert (await client.post("/mcp", json=batch, headers=headers)).status_code == 403
        async with mcp_session(client, read_only) as session:
            result = await session.call_tool("search_products", {"query": "yoga mat"})
            assert not result.isError and "AR-1301" in result.content[0].text


async def test_each_principal_gets_its_own_session_and_cart(idp):
    async with running_app(idp) as client:
        async with mcp_session(client, idp.token(KID, sub="cust-a")) as a:
            await a.call_tool("search_products", {"query": "yoga mat"})
            added = await a.call_tool("add_to_cart", {"product_id": "AR-1301"})
            assert "Added AR-1301" in added.content[0].text
        async with mcp_session(client, idp.token(KID, sub="cust-b")) as b:
            assert (await b.call_tool("whoami", {})).content[0].text == "cust-b"
            cart_b = (await b.call_tool("get_cart", {})).content[0].text
            assert "AR-1301" not in cart_b
            # cust-b never searched: provenance is per principal too.
            held = (await b.call_tool("add_to_cart", {"product_id": "AR-1301"})).content[0].text
            assert "was not returned by catalog" in held


async def test_rfc9728_path_suffixed_metadata_is_served(idp):
    async with running_app(idp) as client:
        response = await client.get("/.well-known/oauth-protected-resource/mcp")
    assert response.status_code == 200
    assert response.json()["resource"] == SETTINGS.resource
    assert "header" in response.json().get("bearer_methods_supported", [])
    assert BASE  # the app is reachable without a token only on this path
