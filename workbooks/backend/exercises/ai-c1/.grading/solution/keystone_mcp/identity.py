"""Delegation tokens: the agent gateway mints one per agent session, on behalf of a signed-in user.

Format: base64url(JSON claims) + "." + base64url(HMAC-SHA256(secret, payload)). Claims:
  sub     user id the agent acts for          tenant  the user's tenant
  scopes  e.g. ["crm.read", "crm.write"]       agent   agent app id, e.g. "sales-assistant"
  exp     expiry, unix seconds
In production this is an OAuth token exchange; the shape of the problem is the same.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
from dataclasses import dataclass


class InvalidDelegation(Exception):
    """The token is malformed, has a bad signature, or has expired."""


@dataclass(frozen=True)
class Identity:
    user_id: str
    tenant: str
    scopes: frozenset[str]
    agent_id: str


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sign_delegation(claims: dict, secret: bytes) -> str:
    payload = _b64(json.dumps(claims, sort_keys=True, separators=(",", ":")).encode())
    sig = _b64(hmac.new(secret, payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{sig}"


def verify_delegation(token: str, secret: bytes, now: float) -> Identity:
    """Return the Identity in a valid token; raise InvalidDelegation otherwise."""
    payload, dot, sig = token.partition(".")
    if not dot or not payload or not sig:
        raise InvalidDelegation("malformed token")
    expected = _b64(hmac.new(secret, payload.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, sig):
        raise InvalidDelegation("bad signature")
    try:
        claims = json.loads(_unb64(payload))
    except (binascii.Error, ValueError) as exc:
        raise InvalidDelegation("malformed claims") from exc
    for k in ("sub", "tenant", "scopes", "agent", "exp"):
        if k not in claims:
            raise InvalidDelegation(f"missing claim {k}")
    if not isinstance(claims["exp"], (int, float)) or claims["exp"] <= now:
        raise InvalidDelegation("token expired")
    return Identity(str(claims["sub"]), str(claims["tenant"]), frozenset(claims["scopes"]), str(claims["agent"]))
