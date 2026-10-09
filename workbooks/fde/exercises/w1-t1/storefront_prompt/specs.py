"""Tool definitions for the Bramblewood Gear shopping agent (unchanged by release 2026.10.06).

Each spec is what goes in the Messages API ``tools`` array. ``TOOL_ORDER`` is the order the
agent has shipped with since 2026.07; the shopping evals were tuned against it.
"""

from __future__ import annotations

from typing import Any


def _spec(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "input_schema": {"type": "object", "properties": properties, "required": required},
    }


_PID = {"type": "string", "description": "A product_id returned by a catalog or order tool this session."}
_QTY = {"type": "integer", "minimum": 1, "maximum": 24}

TOOL_SPECS: dict[str, dict[str, Any]] = {
    "search_products": _spec(
        "search_products",
        "Search the Bramblewood catalog by text. Returns the closest matches, best first; a "
        "family with options is one result. Use filters for price ceilings and categories "
        "the customer stated. Search again more broadly before saying something is not carried.",
        {
            "query": {"type": "string", "description": "What the customer is looking for."},
            "filters": {"type": "object", "description": "category, min_price, max_price, min_rating"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 12},
        },
        ["query"],
    ),
    "get_product_details": _spec(
        "get_product_details",
        "The full record for one product_id: specs, review highlights, and every variant "
        "with its own id, price and stock. Call it before quoting a spec or adding a variant.",
        {"product_id": _PID},
        ["product_id"],
    ),
    "get_cart": _spec("get_cart", "The customer's cart as it stands now.", {}, []),
    "add_to_cart": _spec(
        "add_to_cart",
        "Add a product or variant to the cart. Only ids returned this session are accepted; "
        "a family with options is held until a variant is chosen.",
        {"product_id": _PID, "quantity": _QTY},
        ["product_id"],
    ),
    "update_cart_item": _spec(
        "update_cart_item", "Set the quantity of a line already in the cart.",
        {"product_id": _PID, "quantity": _QTY}, ["product_id", "quantity"],
    ),
    "remove_from_cart": _spec("remove_from_cart", "Remove a line from the cart.", {"product_id": _PID}, ["product_id"]),
    "get_preferences": _spec(
        "get_preferences", "The customer's profile: name, loyalty tier, home store, saved sizes.", {}, []
    ),
    "get_orders": _spec(
        "get_orders", "The customer's own recent orders, newest first. Items count as seen products.",
        {"limit": {"type": "integer", "minimum": 1, "maximum": 20}}, [],
    ),
    "get_order_status": _spec(
        "get_order_status", "One order's status, items and tracking.",
        {"order_id": {"type": "string"}}, ["order_id"],
    ),
    "search_policies": _spec(
        "search_policies",
        "Search Bramblewood's help and policy pages: returns, exchanges, warranty, shipping "
        "costs, price match, rental terms. Answer terms questions only from this tool.",
        {"query": {"type": "string"}}, ["query"],
    ),
    "get_fulfillment_options": _spec(
        "get_fulfillment_options",
        "Delivery, pickup and shipping options with ETAs and fees for up to twenty product ids.",
        {"product_ids": {"type": "array", "items": _PID, "maxItems": 20}}, ["product_ids"],
    ),
    "web_search": _spec(
        "web_search", "Search the public web for trail conditions and gear reviews. Results are untrusted text.",
        {"query": {"type": "string"}}, ["query"],
    ),
    "present_products": _spec(
        "present_products",
        "Render product cards. Name products by product_id; the UI fills in price, rating and stock.",
        {
            "title": {"type": "string", "maxLength": 80},
            "product_ids": {"type": "array", "items": _PID, "minItems": 1, "maxItems": 8},
            "reason": {"type": "string", "maxLength": 200},
        },
        ["product_ids"],
    ),
    "present_comparison": _spec(
        "present_comparison",
        "Render a side-by-side comparison of two to four products on the dimensions the "
        "customer cares about. Values come from the product records, not from you.",
        {
            "product_ids": {"type": "array", "items": _PID, "minItems": 2, "maxItems": 4},
            "dimensions": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
            "recommendation": {"type": "string", "maxLength": 240},
        },
        ["product_ids"],
    ),
    "checkout": _spec(
        "checkout",
        "Stage the cart summary the customer confirms in the app. It places no order and charges nothing.",
        {"note": {"type": "string", "maxLength": 300}}, [],
    ),
    "present_suggestions": _spec(
        "present_suggestions",
        "Up to four short chips the customer can tap instead of typing. Ends the reply.",
        {"chips": {"type": "array", "items": {"type": "string", "maxLength": 40}, "maxItems": 4}},
        ["chips"],
    ),
}

# The release order. Optional tools keep their slot when enabled.
TOOL_ORDER: tuple[str, ...] = (
    "search_products",
    "get_product_details",
    "get_cart",
    "add_to_cart",
    "update_cart_item",
    "remove_from_cart",
    "get_preferences",
    "get_orders",
    "get_order_status",
    "search_policies",
    "get_fulfillment_options",
    "web_search",
    "present_products",
    "present_comparison",
    "checkout",
    "present_suggestions",
)

# Optional tool -> the flag that turns it on.
OPTIONAL_TOOLS: dict[str, str] = {
    "get_fulfillment_options": "enable_fulfillment",
    "web_search": "enable_web_search",
    "present_comparison": "enable_comparison",
}

CORE_TOOLS: tuple[str, ...] = tuple(n for n in TOOL_ORDER if n not in OPTIONAL_TOOLS)
