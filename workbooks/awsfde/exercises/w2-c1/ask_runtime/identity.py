"""Caller identity inside the agent container.

The runtime is configured with a customJWTAuthorizer (Cognito). AgentCore Runtime validates the
bearer token (signature, issuer via discovery URL, audience/client) BEFORE the request reaches this
container, and passes the Authorization header through because it is on the runtime's request
header allowlist. So the container only decodes the payload of a token that was already verified.

Never call this on a token that did not come through a runtime with JWT inbound auth configured.
"""

from __future__ import annotations

import base64
import json


def header(headers: dict, name: str) -> str | None:
    """Case-insensitive header lookup (HTTP header names are case-insensitive)."""
    want = name.lower()
    for k, v in headers.items():
        if k.lower() == want:
            return v
    return None


def bearer_claims(headers: dict) -> dict | None:
    """Claims of the (already validated) bearer token, or None when there is no bearer token."""
    auth = header(headers, "Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    parts = auth[len("Bearer "):].strip().split(".")
    if len(parts) != 3:
        return None
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
    except (ValueError, UnicodeDecodeError):
        return None
