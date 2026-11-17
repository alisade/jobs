"""Lambda entry point for the Gateway target.

AgentCore Gateway invokes the function with:
- event:   the tool arguments (a map of the tool's inputSchema properties)
- context: context.client_context.custom carries bedrockAgentCoreToolName and friends
"""

from __future__ import annotations

import json
import logging

from .tools import HANDLERS, NotFound

log = logging.getLogger("tidewater.order_tools")
log.setLevel(logging.INFO)


def tool_name_from_context(context) -> str:
    full = context.client_context.custom["bedrockAgentCoreToolName"]
    # visible tool names look like "orders_search"; keep the part after the prefix
    return full.split("_")[-1]


def lambda_handler(event, context):
    custom = context.client_context.custom
    name = tool_name_from_context(context)
    log.info(json.dumps({"event": "tool_call", "tool": name, "gateway": custom.get("bedrockAgentCoreGatewayId"),
                         "target": custom.get("bedrockAgentCoreTargetId"),
                         "mcp_message_id": custom.get("bedrockAgentCoreMcpMessageId")}))
    fn = HANDLERS.get(name)
    if fn is None:
        raise ValueError(f"Unknown tool: {name}")
    try:
        return fn(event)
    except NotFound as e:
        return {"error": {"code": "NOT_FOUND", "message": str(e)}}
