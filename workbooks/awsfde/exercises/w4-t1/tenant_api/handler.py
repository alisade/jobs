"""GET /shipments for the caller's tenant (HTTP API payload 2.0, Cognito JWT authorizer)."""

from __future__ import annotations

import json
import logging
import pathlib
from typing import Any

from .resolver import resolve_tenant

log = logging.getLogger("tidewater.shipments")
DATA = json.loads((pathlib.Path(__file__).resolve().parent.parent / "data" / "shipments.json").read_text())


def _resp(code: int, body: dict) -> dict:
    return {"statusCode": code, "headers": {"content-type": "application/json", "cache-control": "no-store"},
            "body": json.dumps(body)}


def handler(event: dict, context: Any = None) -> dict:
    claims = (((event.get("requestContext") or {}).get("authorizer") or {}).get("jwt") or {}).get("claims") or {}
    tenant, source = resolve_tenant(claims)
    log.info(json.dumps({"event": "tenant_resolved", "sub": claims.get("sub"), "token_use": claims.get("token_use"),
                         "tenant_id": tenant, "source": source}))
    if not tenant:
        return _resp(403, {"error": "no tenant for this caller"})
    return _resp(200, {"tenant_id": tenant, "shipments": DATA.get(tenant, [])})
