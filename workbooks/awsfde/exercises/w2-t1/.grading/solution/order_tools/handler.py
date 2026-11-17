"""Lambda entry point for the Gateway target.

AgentCore Gateway invokes the function with:
- event:   the tool arguments (a map of the tool's inputSchema properties)
- context: context.client_context.custom carries bedrockAgentCoreToolName and friends

The tool name arrives as "<targetName>___<toolName>" (three underscores). Target names and tool
names may themselves contain single underscores and hyphens, so split once on the delimiter.
"""

from __future__ import annotations

import json
import logging
import pathlib

import jsonschema

from .tools import HANDLERS, NotFound

log = logging.getLogger("tidewater.order_tools")
log.setLevel(logging.INFO)

DELIMITER = "___"
SCHEMAS = {t["name"]: t["inputSchema"] for t in
           json.loads((pathlib.Path(__file__).resolve().parent / "tools.json").read_text())}


def tool_name_from_context(context) -> str:
    full = context.client_context.custom["bedrockAgentCoreToolName"]
    _, sep, tool = full.partition(DELIMITER)
    return tool if sep else full  # no prefix: direct invoke (tests, console)


def _error(code: str, message: str, **extra) -> dict:
    return {"error": dict({"code": code, "message": message}, **extra)}


def lambda_handler(event, context):
    custom = context.client_context.custom
    name = tool_name_from_context(context)
    log.info(json.dumps({"event": "tool_call", "tool": name, "full_name": custom.get("bedrockAgentCoreToolName"),
                         "gateway": custom.get("bedrockAgentCoreGatewayId"),
                         "target": custom.get("bedrockAgentCoreTargetId"),
                         "mcp_message_id": custom.get("bedrockAgentCoreMcpMessageId")}))
    fn = HANDLERS.get(name)
    if fn is None:
        log.warning(json.dumps({"event": "unknown_tool", "tool": name}))
        return _error("UNKNOWN_TOOL", f"Unknown tool {name!r}.", available=sorted(HANDLERS))
    args = event if isinstance(event, dict) else {}
    try:
        jsonschema.validate(args, SCHEMAS[name])
    except jsonschema.ValidationError as e:
        return _error("INVALID_INPUT", f"Invalid input for {name}: {e.message}")
    try:
        return fn(args)
    except NotFound as e:
        return _error("NOT_FOUND", str(e))
