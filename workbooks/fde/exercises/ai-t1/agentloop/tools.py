"""Lumen Home's tools as the turn loop sees them. Given; do not change.

In production each tool calls an internal service. For replay, ``ReplayToolBox`` answers
from the recorded outcome of each call: an output, an exception the service raised, or a
delay (a slow upstream).
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_catalog",
        "description": "Search Lumen Home's catalog. Returns up to 8 products with sku, title, price.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "check_stock",
        "description": "Stock level for one sku at the customer's nearest store and online.",
        "input_schema": {
            "type": "object",
            "properties": {"sku": {"type": "string"}},
            "required": ["sku"],
        },
    },
    {
        "name": "shipping_estimate",
        "description": "Delivery date estimate for one sku to the customer's saved address.",
        "input_schema": {
            "type": "object",
            "properties": {"sku": {"type": "string"}},
            "required": ["sku"],
        },
    },
    {
        "name": "get_order",
        "description": "One of the customer's own orders by order id.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
]


class InventoryTimeout(Exception):
    """The inventory service did not answer in time."""


class UpstreamError(Exception):
    """An internal service answered 5xx."""


class UnknownTool(KeyError):
    """The model named a tool this deployment does not serve."""


ERRORS = {"InventoryTimeout": InventoryTimeout, "UpstreamError": UpstreamError}


def call_key(name: str, tool_input: dict[str, Any]) -> str:
    return name + " " + json.dumps(tool_input, sort_keys=True)


class ReplayToolBox:
    """``recorded`` maps ``call_key(name, input)`` to one of ``{"output": str}``,
    ``{"error": "<class name>", "message": str}`` or ``{"delay": seconds, "output": str}``."""

    def __init__(self, recorded: dict[str, dict[str, Any]]):
        self._recorded = recorded
        self.calls: list[str] = []

    async def call(self, name: str, tool_input: dict[str, Any]) -> str:
        if name not in {t["name"] for t in TOOLS}:
            raise UnknownTool(name)
        key = call_key(name, tool_input)
        self.calls.append(key)
        outcome = self._recorded.get(key, {"output": f"{name}: no data"})
        if outcome.get("delay"):
            await asyncio.sleep(float(outcome["delay"]))
        if outcome.get("error"):
            raise ERRORS[outcome["error"]](outcome.get("message", outcome["error"]))
        return str(outcome["output"])
