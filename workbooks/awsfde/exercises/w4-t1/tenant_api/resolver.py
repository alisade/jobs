"""Which tenant is this request for."""

from __future__ import annotations

import os


def resolve_tenant(claims: dict) -> tuple[str | None, str]:
    """Return (tenant_id, source) from the verified JWT claims the authorizer passed us."""
    if claims.get("tenant_id"):
        return claims["tenant_id"], "claim:tenant_id"
    if claims.get("custom:tenant_id"):
        return claims["custom:tenant_id"], "claim:custom:tenant_id"
    # Pilot: Acme was the only tenant and some test clients sent no claims. Keep the API usable.
    default = os.environ.get("DEFAULT_TENANT")
    if default:
        return default, "env:DEFAULT_TENANT"
    return None, "none"
