"""The two tools the assistant may call. Tool *specs* are what the model sees; the *handlers*
run in our code with the verified tenant from CallerContext."""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable

from .context import CallerContext

LOOKUP_SHIPMENT_SPEC = {
    "toolSpec": {
        "name": "lookup_shipment",
        "description": (
            "Look up one shipment of the caller's company by its shipment id (format SH-12345). "
            "Returns status, origin, destination and ETA. Use it whenever the user asks where a "
            "shipment is or when it arrives."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "shipment_id": {"type": "string", "pattern": "^SH-[0-9]{5}$"},
                },
                "required": ["shipment_id"],
                "additionalProperties": False,
            }
        },
    }
}

CREATE_TICKET_SPEC = {
    "toolSpec": {
        "name": "create_ticket",
        "description": (
            "Open a support ticket for the caller's company when the user reports a problem the "
            "assistant cannot solve. Summarize the problem in one or two sentences."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "minLength": 10, "maxLength": 500},
                    "priority": {"type": "string", "enum": ["low", "normal", "high"]},
                    "shipment_id": {"type": "string", "pattern": "^SH-[0-9]{5}$"},
                },
                "required": ["summary", "priority"],
                "additionalProperties": False,
            }
        },
    }
}

TOOL_SPECS = [LOOKUP_SHIPMENT_SPEC, CREATE_TICKET_SPEC]


class ToolError(Exception):
    """A failure the model should see and can recover from (bad id, not found)."""


def lookup_shipment(table: Any, ctx: CallerContext, args: dict) -> dict:
    item = table.get_item(
        Key={"pk": f"TENANT#{ctx.tenant_id}", "sk": f"SHIPMENT#{args['shipment_id']}"}
    ).get("Item")
    if not item:
        raise ToolError(f"No shipment {args['shipment_id']} for this account.")
    return {
        "shipment_id": args["shipment_id"],
        "status": item["status"],
        "origin": item["origin"],
        "destination": item["destination"],
        "eta": item["eta"],
    }


def create_ticket(table: Any, ctx: CallerContext, args: dict) -> dict:
    ticket_id = "TK-" + uuid.uuid4().hex[:8].upper()
    table.put_item(
        Item={
            "pk": f"TENANT#{ctx.tenant_id}",
            "sk": f"TICKET#{ticket_id}",
            "summary": args["summary"],
            "priority": args["priority"],
            "shipment_id": args.get("shipment_id", ""),
            "opened_by": ctx.user_id,
            "opened_at": int(time.time()),
        },
        ConditionExpression="attribute_not_exists(pk)",
    )
    return {"ticket_id": ticket_id, "status": "open"}


HANDLERS: dict[str, Callable[[Any, CallerContext, dict], dict]] = {
    "lookup_shipment": lookup_shipment,
    "create_ticket": create_ticket,
}
