"""Cognito pre token generation trigger (event version V2_0).

Adds the tenant_id claim to the ID token AND the access token from the user-to-tenant mapping item.
Unmapped users fail closed: raising makes Cognito reject the sign-in.
"""

from __future__ import annotations

import os
from typing import Any

import boto3

from .keys import check_tenant, user_map_key


class TenantMappingError(Exception):
    pass


def _table() -> Any:
    return boto3.resource("dynamodb").Table(os.environ.get("TABLE_NAME", "tidewater-ops"))


def handler(event: dict, context: Any = None, table: Any = None) -> dict:
    if event.get("version") != "2":
        raise TenantMappingError("pre token generation trigger must be configured with LambdaVersion V2_0")
    table = table or _table()
    sub = event["request"]["userAttributes"]["sub"]
    item = table.get_item(Key=user_map_key(sub)).get("Item")
    if not item or not item.get("tenant_id"):
        raise TenantMappingError(f"user {sub} is not mapped to a tenant")
    tenant = check_tenant(item["tenant_id"])
    claims = {"tenant_id": tenant}
    event.setdefault("response", {})
    event["response"]["claimsAndScopeOverrideDetails"] = {
        "idTokenGeneration": {"claimsToAddOrOverride": dict(claims)},
        "accessTokenGeneration": {"claimsToAddOrOverride": dict(claims)},
    }
    return event
