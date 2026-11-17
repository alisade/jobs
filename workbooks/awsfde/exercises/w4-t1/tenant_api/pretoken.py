"""tw-pre-token-generation: adds the tenant_id claim to user pool tokens.

Written for the V1_0 trigger event during the pilot (ID token customization).
"""

from __future__ import annotations

from typing import Any


class TenantMappingError(Exception):
    pass


def handler(event: dict, context: Any = None) -> dict:
    tenant = event["request"]["userAttributes"].get("custom:tenant_id")
    if not tenant:
        raise TenantMappingError(f"user {event.get('userName')} has no custom:tenant_id")
    event["response"]["claimsOverrideDetails"] = {"claimsToAddOrOverride": {"tenant_id": tenant}}
    return event
