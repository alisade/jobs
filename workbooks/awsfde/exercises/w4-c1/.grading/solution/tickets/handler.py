"""HTTP API (payload 2.0) Lambda for the ticket tool, behind a Cognito JWT authorizer.

Routes:
  GET  /tickets/{ticket_id}              AP1
  GET  /tickets?status=open              AP2
  POST /tools/get_ticket   {"ticket_id"}  AP1, called by the agent's tool layer

The tenant is read ONLY from event.requestContext.authorizer.jwt.claims.tenant_id.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from .keys import status_gsi_pk, ticket_key

log = logging.getLogger("tidewater.tickets")
TENANT_PARAM_NAMES = ("tenant_id", "tenant", "tenantId")


def _resp(code: int, body: dict) -> dict:
    return {"statusCode": code, "headers": {"content-type": "application/json", "cache-control": "no-store"},
            "body": json.dumps(body)}


def tenant_from_event(event: dict) -> str | None:
    claims = (((event.get("requestContext") or {}).get("authorizer") or {}).get("jwt") or {}).get("claims") or {}
    t = claims.get("tenant_id")
    return t if isinstance(t, str) and t else None


def _public(item: dict) -> dict:
    return {k: item[k] for k in ("ticket_id", "status", "created_at", "summary", "shipment_id") if k in item}


def _supplied_tenants(event: dict, body: dict) -> list[str]:
    found = []
    for src in (event.get("pathParameters") or {}, event.get("queryStringParameters") or {}, body):
        for k in TENANT_PARAM_NAMES:
            if isinstance(src, dict) and k in src:
                found.append(str(src[k]))
    return found


def handler(event: dict, context: Any = None, table: Any = None) -> dict:
    table = table or boto3.resource("dynamodb").Table(os.environ.get("TABLE_NAME", "tidewater-ops"))
    tenant = tenant_from_event(event)
    if not tenant:
        return _resp(403, {"error": "no tenant in token"})
    try:
        body = json.loads(event.get("body") or "{}")
    except ValueError:
        return _resp(400, {"error": "body must be JSON"})
    if not isinstance(body, dict):
        return _resp(400, {"error": "body must be a JSON object"})
    supplied = _supplied_tenants(event, body)
    if any(s != tenant for s in supplied):
        log.warning(json.dumps({"event": "tenant_param_ignored", "tenant_id": tenant, "supplied": supplied}))
    route = event.get("routeKey", "")
    try:
        if route in ("GET /tickets/{ticket_id}", "POST /tools/get_ticket"):
            tid = (event.get("pathParameters") or {}).get("ticket_id") if route.startswith("GET") else body.get("ticket_id")
            item = table.get_item(Key=ticket_key(tenant, tid or "")).get("Item")
            if not item:
                return _resp(404, {"error": "ticket not found"})
            return _resp(200, _public(item))
        if route == "GET /tickets":
            status = (event.get("queryStringParameters") or {}).get("status", "open")
            r = table.query(IndexName="gsi1", KeyConditionExpression=Key("gsi1pk").eq(status_gsi_pk(tenant, status)),
                            ScanIndexForward=False, Limit=50)
            return _resp(200, {"tickets": [_public(i) for i in r.get("Items", [])]})
    except ValueError as e:
        return _resp(400, {"error": str(e)})
    return _resp(404, {"error": f"no route {route}"})
