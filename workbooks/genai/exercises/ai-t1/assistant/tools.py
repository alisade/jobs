"""Tool definitions for the Kestrel assistant (complete; do not change)."""

TOOL_DEFS = {
    "search_products": {
        "name": "search_products",
        "description": "Search the Kestrel catalog by keywords. Returns up to 10 products with sku, name and price.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    },
    "check_inventory": {
        "name": "check_inventory",
        "description": "Units available for a sku at a store (3-digit store id).",
        "input_schema": {
            "type": "object",
            "properties": {"sku": {"type": "string"}, "store_id": {"type": "string"}},
            "required": ["sku", "store_id"],
        },
    },
    "get_order_status": {
        "name": "get_order_status",
        "description": "Status of one of the signed-in customer's orders.",
        "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]},
    },
    "start_return": {
        "name": "start_return",
        "description": "Propose a return for a delivered order; the customer confirms it in the app.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}, "reason": {"type": "string"}},
            "required": ["order_id", "reason"],
        },
    },
    "store_hours": {
        "name": "store_hours",
        "description": "Opening hours for a Kestrel store.",
        "input_schema": {"type": "object", "properties": {"store_id": {"type": "string"}}, "required": ["store_id"]},
    },
}

SYSTEM_POLICY = (
    "You are Kestrel Outfitters' shopping assistant for the web shop and the store associate app. "
    "Answer from tool results only and cite the sku for every product you mention. Prices and stock "
    "come from tools, never from memory. Returns need the customer's confirmation in the app. "
    "If you are not sure, say so and offer Talk to a person. "
) * 12  # the real policy is about 4,000 tokens; repeated here to make the prefix realistically large

PRODUCT_GUIDE = (
    "Category guide: tents (1P-6P, footprints, stakes), sleeping (bags by temperature rating, pads by "
    "R-value), lighting, cooking, packs, apparel, furniture. Recommend the smallest product that fits "
    "the stated need and mention one alternative. "
) * 8
