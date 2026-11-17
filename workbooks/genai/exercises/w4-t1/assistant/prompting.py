"""How tool results are written into the model's context."""

from __future__ import annotations

import json

SYSTEM = (
    "You are Kestrel Outfitters' shopping assistant. Answer using the tool results. Cite products as [SKU]. "
    "Only mention promotions that appear in the promotions list."
)


def render_tool_result(records: list[dict]) -> str:
    """Text the model sees for a search_products result (release 2026.11.07 added reviews)."""
    return "search_products result:\n" + json.dumps(records, indent=1)


def render_promotions(promotions: dict[str, dict]) -> str:
    return "active promotions:\n" + json.dumps(list(promotions.values()), indent=1)


def build_prompt(question: str, records: list[dict], promotions: dict[str, dict]) -> str:
    return "\n\n".join([SYSTEM, render_tool_result(records), render_promotions(promotions), "Customer: " + question])
