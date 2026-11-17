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
    """TODO: the tenant_id claim from the JWT authorizer context, or None."""
    raise NotImplementedError



def _public(item: dict) -> dict:
    return {k: item[k] for k in ("ticket_id", "status", "created_at", "summary", "shipment_id") if k in item}


def _supplied_tenants(event: dict, body: dict) -> list[str]:
    """Tenant values a caller put in the path, query string or body (for logging only). TODO"""
    raise NotImplementedError



def handler(event: dict, context: Any = None, table: Any = None) -> dict:
    """TODO: see README. 403 without a tenant claim; tenant values in path/query/body are never used (log them); 404 for a ticket that is not the caller's; 400 for bad input."""
    raise NotImplementedError
