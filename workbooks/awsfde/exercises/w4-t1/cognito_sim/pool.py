"""Token issuance with the pre token generation trigger, the SPA's token choice, the JWT authorizer."""

from __future__ import annotations

import copy
import json
import pathlib
from typing import Any, Callable

ROOT = pathlib.Path(__file__).resolve().parent.parent
ISS = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TideW8ter"


class TokenError(Exception):
    pass


def load(name: str) -> dict:
    return json.loads((ROOT / "config" / name).read_text())


def _event(version: str, user: dict, pool: dict) -> dict:
    attrs = {"sub": user["sub"], "email": user["email"], "email_verified": "true",
             "custom:tenant_id": user["custom:tenant_id"], "cognito:user_status": "CONFIRMED"}
    if user.get("provider"):
        attrs["identities"] = json.dumps([{"providerName": user["provider"], "providerType":
                                           "SAML" if "saml" in user["provider"] else "OIDC", "primary": "true"}])
    ev = {"version": version, "region": "us-east-1", "userPoolId": pool["Id"], "userName": user["username"],
          "triggerSource": "TokenGeneration_HostedAuth" if user.get("provider") else "TokenGeneration_Authentication",
          "callerContext": {"awsSdkVersion": "aws-sdk-unknown-unknown", "clientId": pool["AppClient"]["ClientId"]},
          "request": {"userAttributes": attrs,
                      "groupConfiguration": {"groupsToOverride": [], "iamRolesToOverride": [], "preferredRole": None}}}
    if version == "1":
        ev["response"] = {"claimsOverrideDetails": None}
    else:
        ev["request"]["scopes"] = ["openid", "email", "ask/shipments.read"]
        ev["response"] = {"claimsAndScopeOverrideDetails": None}
    return ev


def issue_tokens(user: dict, trigger: Callable[[dict, Any], dict], pool: dict | None = None) -> dict:
    """Sign a user in: returns {"id": claims, "access": claims, "event_version": "1"|"2"}."""
    pool = pool or load("user-pool.json")
    client = pool["AppClient"]["ClientId"]
    lv = pool["LambdaConfig"]["PreTokenGenerationConfig"]["LambdaVersion"]
    if lv not in ("V1_0", "V2_0"):
        raise TokenError(f"unsupported LambdaVersion {lv}")
    if lv == "V2_0" and pool.get("UserPoolTier") not in ("ESSENTIALS", "PLUS"):
        raise TokenError("V2_0 pre token generation events need the Essentials or Plus feature plan")
    idt = {"sub": user["sub"], "iss": ISS, "aud": client, "token_use": "id", "auth_time": 1763049600,
           "cognito:username": user["username"], "email": user["email"]}
    if "custom:tenant_id" in pool["AppClient"]["ReadAttributes"]:
        idt["custom:tenant_id"] = user["custom:tenant_id"]
    acc = {"sub": user["sub"], "iss": ISS, "client_id": client, "token_use": "access",
           "scope": "openid email ask/shipments.read", "username": user["username"], "auth_time": 1763049600}
    version = "1" if lv == "V1_0" else "2"
    out = trigger(_event(version, user, pool), None) or {}
    resp = out.get("response") or {}
    if version == "1":
        idt.update(((resp.get("claimsOverrideDetails") or {}).get("claimsToAddOrOverride")) or {})
    else:
        d = resp.get("claimsAndScopeOverrideDetails") or {}
        idt.update(((d.get("idTokenGeneration") or {}).get("claimsToAddOrOverride")) or {})
        acc.update(((d.get("accessTokenGeneration") or {}).get("claimsToAddOrOverride")) or {})
    return {"id": idt, "access": acc, "event_version": version}


def spa_token(tokens: dict, frontend: dict | None = None) -> dict:
    """The token the SPA puts in the Authorization header."""
    frontend = frontend or load("frontend.json")
    return tokens["access"] if frontend.get("api_token") == "access" else tokens["id"]


def jwt_authorizer(token: dict, pool: dict | None = None) -> dict:
    """HTTP API JWT authorizer: issuer + audience check, then claims into the request context."""
    pool = pool or load("user-pool.json")
    client = pool["AppClient"]["ClientId"]
    if token.get("iss") != ISS:
        raise TokenError("issuer mismatch")
    aud = token.get("aud") if token.get("token_use") == "id" else token.get("client_id")
    if aud != client:
        raise TokenError("audience mismatch")
    return {"version": "2.0", "routeKey": "GET /shipments", "rawPath": "/shipments",
            "requestContext": {"authorizer": {"jwt": {"claims": {k: (v if isinstance(v, str) else json.dumps(v))
                                                                  for k, v in copy.deepcopy(token).items()},
                                                       "scopes": token.get("scope", "").split() or None}},
                               "http": {"method": "GET"}}}
