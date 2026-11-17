"""Single-table key design for tickets in table tidewater-ops.

Access patterns (see README):
  AP1 get one ticket by id                      GetItem  pk=TENANT#<t>  sk=TICKET#<id>
  AP2 list a tenant's tickets by status, newest Query    GSI1 gsi1pk=TENANT#<t>#STATUS#<status>, gsi1sk desc
  AP3 list a tenant's tickets for a shipment    Query    GSI2 gsi2pk=TENANT#<t>#SHIPMENT#<id>
  AP4 map a Cognito user to a tenant            GetItem  pk=USER#<sub>  sk=TENANT
"""

from __future__ import annotations

import re

TENANT_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
TICKET_RE = re.compile(r"^TK-[0-9A-F]{8}$")


def check_tenant(tenant_id: str) -> str:
    if not isinstance(tenant_id, str) or not TENANT_RE.match(tenant_id):
        raise ValueError(f"invalid tenant id {tenant_id!r}")
    return tenant_id


def tenant_pk(tenant_id: str) -> str:
    return f"TENANT#{check_tenant(tenant_id)}"


def ticket_key(tenant_id: str, ticket_id: str) -> dict:
    if not TICKET_RE.match(ticket_id or ""):
        raise ValueError(f"invalid ticket id {ticket_id!r}")
    return {"pk": tenant_pk(tenant_id), "sk": f"TICKET#{ticket_id}"}


def status_gsi_pk(tenant_id: str, status: str) -> str:
    if status not in ("open", "pending", "closed"):
        raise ValueError(f"invalid status {status!r}")
    return f"{tenant_pk(tenant_id)}#STATUS#{status}"


def shipment_gsi_pk(tenant_id: str, shipment_id: str) -> str:
    return f"{tenant_pk(tenant_id)}#SHIPMENT#{shipment_id}"


def ticket_item(tenant_id: str, ticket_id: str, status: str, created_at: str, summary: str,
                shipment_id: str | None = None) -> dict:
    item = {**ticket_key(tenant_id, ticket_id), "tenant_id": tenant_id, "ticket_id": ticket_id,
            "status": status, "created_at": created_at, "summary": summary,
            "gsi1pk": status_gsi_pk(tenant_id, status), "gsi1sk": f"{created_at}#{ticket_id}"}
    if shipment_id:
        item["shipment_id"] = shipment_id
        item["gsi2pk"] = shipment_gsi_pk(tenant_id, shipment_id)
        item["gsi2sk"] = f"{created_at}#{ticket_id}"
    return item


def user_map_key(sub: str) -> dict:
    return {"pk": f"USER#{sub}", "sk": "TENANT"}
