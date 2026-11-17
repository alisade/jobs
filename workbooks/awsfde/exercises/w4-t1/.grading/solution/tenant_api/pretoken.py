"""tw-pre-token-generation: adds the tenant_id claim to user pool tokens.

Configured as a V2_0 trigger (LambdaVersion V2_0, Essentials feature plan) so the claim goes into
BOTH the ID token and the access token. A V1_0 event can only customize the ID token.
"""

from __future__ import annotations

from typing import Any


class TenantMappingError(Exception):
    pass


def handler(event: dict, context: Any = None) -> dict:
    tenant = event["request"]["userAttributes"].get("custom:tenant_id")
    if not tenant:
        raise TenantMappingError(f"user {event.get('userName')} has no custom:tenant_id")
    claims = {"tenant_id": tenant}
    if event.get("version") == "1":
        # Tolerated during the rollout so a config rollback does not break sign-in; ID token only.
        event["response"]["claimsOverrideDetails"] = {"claimsToAddOrOverride": claims}
        return event
    event["response"]["claimsAndScopeOverrideDetails"] = {
        "idTokenGeneration": {"claimsToAddOrOverride": dict(claims)},
        "accessTokenGeneration": {"claimsToAddOrOverride": dict(claims)},
    }
    return event
