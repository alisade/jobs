"""Hidden checks for w4-t1: V2_0 trigger, both tokens carry the claim, fail closed, no default tenant."""

from __future__ import annotations

import json
import pathlib

import pytest

from cognito_sim.pool import issue_tokens, jwt_authorizer, load, spa_token
from tenant_api import pretoken
from tenant_api.handler import handler
from tenant_api.resolver import resolve_tenant

ROOT = pathlib.Path(__file__).resolve().parent.parent
USERS = json.loads((ROOT / "data" / "users.json").read_text())


def v2_event(attrs):
    return {"version": "2", "triggerSource": "TokenGeneration_HostedAuth", "region": "us-east-1",
            "userPoolId": "us-east-1_TideW8ter", "userName": "u", "callerContext": {"clientId": "c"},
            "request": {"userAttributes": attrs, "groupConfiguration": {}, "scopes": ["openid"]},
            "response": {"claimsAndScopeOverrideDetails": None}}


def test_pool_uses_v2_trigger_event():
    assert load("user-pool.json")["LambdaConfig"]["PreTokenGenerationConfig"]["LambdaVersion"] == "V2_0"


def test_trigger_v2_response_shape():
    out = pretoken.handler(v2_event({"sub": "s", "custom:tenant_id": "corvid-logistics"}))
    d = out["response"]["claimsAndScopeOverrideDetails"]
    assert d["idTokenGeneration"]["claimsToAddOrOverride"]["tenant_id"] == "corvid-logistics"
    assert d["accessTokenGeneration"]["claimsToAddOrOverride"]["tenant_id"] == "corvid-logistics"


def test_trigger_unmapped_user_fails_closed():
    with pytest.raises(Exception):
        pretoken.handler(v2_event({"sub": "s"}))


@pytest.mark.parametrize("u", USERS, ids=[u["username"] for u in USERS])
def test_access_token_carries_tenant(u):
    tokens = issue_tokens(u, pretoken.handler)
    assert tokens["access"].get("tenant_id") == u["custom:tenant_id"]
    assert tokens["id"].get("tenant_id") == u["custom:tenant_id"]


def test_lambda_env_has_no_default_tenant():
    assert "DEFAULT_TENANT" not in load("lambda-env.json")


def test_resolver_fails_closed_even_with_default_env(monkeypatch):
    monkeypatch.setenv("DEFAULT_TENANT", "acme-foods")
    assert resolve_tenant({"sub": "x", "token_use": "access"})[0] is None


def test_handler_403_without_tenant_claim(monkeypatch):
    monkeypatch.setenv("DEFAULT_TENANT", "acme-foods")
    ev = {"requestContext": {"authorizer": {"jwt": {"claims": {"sub": "x", "token_use": "access"}}}}}
    r = handler(ev)
    assert r["statusCode"] == 403 and "SH-10001" not in r["body"]


@pytest.mark.parametrize("token_choice", ["access", "id"])
def test_every_user_served_own_tenant(token_choice, monkeypatch):
    for k, v in load("lambda-env.json").items():
        if not k.startswith("_"):
            monkeypatch.setenv(k, v)
    for u in USERS:
        tokens = issue_tokens(u, pretoken.handler)
        r = handler(jwt_authorizer(spa_token(tokens, {"api_token": token_choice})))
        assert r["statusCode"] == 200, u["username"]
        assert json.loads(r["body"])["tenant_id"] == u["custom:tenant_id"], u["username"]


def test_guard_frontend_still_sends_access_tokens():
    assert load("frontend.json")["api_token"] == "access", "the SR-77 change was right; do not revert it"
