"""Tool definitions the model sees (complete). Execution and policy live in agent.py."""

READ_TOOLS = {"search_products", "check_inventory", "get_order_status"}
WRITE_TOOLS = {"start_return"}

TOOLS = [
    {
        "name": "search_products",
        "description": "Search the Kestrel catalog by keywords. Returns up to 10 products with sku, name and price.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Keywords, e.g. 'two person tent'"}},
            "required": ["query"],
        },
    },
    {
        "name": "check_inventory",
        "description": "Units available for a sku at a store (3-digit store id).",
        "input_schema": {
            "type": "object",
            "properties": {"sku": {"type": "string"}, "store_id": {"type": "string"}},
            "required": ["sku", "store_id"],
        },
    },
    {
        "name": "get_order_status",
        "description": "Status of one of the signed-in customer's orders.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "start_return",
        "description": (
            "Propose a return for a delivered order of the signed-in customer. This does not start the "
            "return: the customer must confirm it in the app first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}, "reason": {"type": "string"}},
            "required": ["order_id", "reason"],
        },
    },
]

SYSTEM_PROMPT = (
    "You are Kestrel Outfitters' shopping assistant. Answer from tool results only. "
    "Returns need the customer's confirmation in the app; never claim a return has started "
    "until a tool result says so."
)
