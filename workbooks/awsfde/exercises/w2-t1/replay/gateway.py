"""Emulates what AgentCore Gateway does for a Lambda target, closely enough to debug the function:

- tools/list answers from the target's tool schema, with each name prefixed "<targetName>___".
- tools/call invokes the Lambda with event = the tool arguments and a context whose
  client_context.custom carries bedrockAgentCoreToolName ("<targetName>___<toolName>"), the gateway id,
  target id, MCP message id, message version and request id (see the Gateway Lambda target docs).
- A Lambda exception or a result carrying an "error" object comes back to the agent as an MCP tool
  result with isError true (the exact gateway error text is simplified here).
"""

from __future__ import annotations

import importlib
import json
import logging
import pathlib
import sys
import uuid
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET_NAME = "tw_orders"
GATEWAY_ID = "tw-ask-acme-gw-k3j9x2m4pq"
TARGET_ID = "TGT7QH2LM9"


@dataclass
class ClientContext:
    custom: dict


@dataclass
class FakeLambdaContext:
    client_context: ClientContext
    aws_request_id: str
    function_name: str = "tw-order-tools-prod"


def tool_defs() -> list[dict]:
    return json.loads((ROOT / "order_tools" / "tools.json").read_text())


def make_context(full_name: str, mcp_id: str) -> FakeLambdaContext:
    rid = str(uuid.uuid5(uuid.NAMESPACE_URL, full_name + mcp_id))
    return FakeLambdaContext(ClientContext({
        "bedrockAgentCoreMessageVersion": "1.0",
        "bedrockAgentCoreAwsRequestId": rid,
        "bedrockAgentCoreMcpMessageId": mcp_id,
        "bedrockAgentCoreGatewayId": GATEWAY_ID,
        "bedrockAgentCoreTargetId": TARGET_ID,
        "bedrockAgentCoreToolName": full_name,
    }), aws_request_id=rid)


def load_handler(root: pathlib.Path = ROOT):
    sys.path.insert(0, str(root))
    for k in [k for k in sys.modules if k == "order_tools" or k.startswith("order_tools.")]:
        del sys.modules[k]
    return importlib.import_module("order_tools.handler").lambda_handler


def call(handler, full_name: str, arguments: dict, mcp_id: str) -> dict:
    """One tools/call through the emulated gateway; returns the MCP result object."""
    ctx = make_context(full_name, mcp_id)
    try:
        out = handler(arguments, ctx)
    except Exception as e:  # the gateway turns a function error into a tool error
        logging.getLogger("tidewater.order_tools").error(
            f"[ERROR] {type(e).__name__}: {e} RequestId: {ctx.aws_request_id} (function error, Unhandled)")
        return {"isError": True, "content": [{"type": "text", "text": f"Lambda function error: {type(e).__name__}: {e}"}]}
    if isinstance(out, dict) and "error" in out:
        return {"isError": True, "content": [{"type": "text", "text": json.dumps(out["error"])}]}
    return {"isError": False, "content": [{"type": "text", "text": json.dumps(out)}]}


def tools_list() -> dict:
    return {"tools": [dict(t, name=f"{TARGET_NAME}___{t['name']}") for t in tool_defs()]}


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(record.getMessage())
