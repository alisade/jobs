"""Signed customer claims. Given and correct; not the fault.

The Managed Agents session carries one vault credential: a short-lived claim the
storefront's login service signs for the customer. Format: ``<payload>.<sig>``, both
base64url, payload ``{"sub": <customer id>, "exp": <unix seconds>}``, sig HMAC-SHA256.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time


class InvalidClaim(Exception):
    pass


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def sign_claim(sub: str, secret: str, ttl_s: int = 900) -> str:
    payload = _b64(json.dumps({"sub": sub, "exp": int(time.time()) + ttl_s}).encode())
    sig = _b64(hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{sig}"


def verify_claim(token: str, secret: str) -> str:
    """The customer id in a valid, unexpired claim; InvalidClaim otherwise."""
    try:
        payload, sig = token.split(".")
    except ValueError as exc:
        raise InvalidClaim("malformed") from exc
    want = _b64(hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(want, sig):
        raise InvalidClaim("bad signature")
    claims = json.loads(_unb64(payload))
    if int(claims.get("exp", 0)) < time.time():
        raise InvalidClaim("expired")
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub:
        raise InvalidClaim("no subject")
    return sub
