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
    """TODO: V2_0 event only; look up the user mapping (AP4); add tenant_id to BOTH the ID token and the access token in response.claimsAndScopeOverrideDetails; unmapped user -> raise TenantMappingError."""
    raise NotImplementedError
