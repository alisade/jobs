"""Which tenant is this request for."""

from __future__ import annotations


def resolve_tenant(claims: dict) -> tuple[str | None, str]:
    """Return (tenant_id, source) from the verified JWT claims the authorizer passed us.

    One source of truth: the tenant_id claim our pre token generation trigger writes into the
    token. No fallbacks: a missing claim is a misconfiguration and the request fails closed (403).
    """
    t = claims.get("tenant_id")
    if isinstance(t, str) and t:
        return t, "claim:tenant_id"
    return None, "none"
