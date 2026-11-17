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
    """AP1 key for one ticket. TODO: validate ticket_id with TICKET_RE (ValueError), pk from tenant_pk()."""
    raise NotImplementedError



def status_gsi_pk(tenant_id: str, status: str) -> str:
    """GSI1 partition key for AP2. TODO: status must be open, pending or closed (ValueError)."""
    raise NotImplementedError



def shipment_gsi_pk(tenant_id: str, shipment_id: str) -> str:
    """GSI2 partition key for AP3. TODO"""
    raise NotImplementedError



def ticket_item(tenant_id: str, ticket_id: str, status: str, created_at: str, summary: str,
                shipment_id: str | None = None) -> dict:
    """The full item for a ticket, with every key attribute AP1-AP3 need. TODO"""
    raise NotImplementedError



def user_map_key(sub: str) -> dict:
    return {"pk": f"USER#{sub}", "sk": "TENANT"}
