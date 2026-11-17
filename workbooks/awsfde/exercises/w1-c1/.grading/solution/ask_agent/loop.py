"""One assistant turn on Amazon Bedrock with the Converse API.

run_turn() sends the user's question, runs any tools the model asks for, sends the results
back, and repeats until the model answers, the guardrail intervenes, or the round limit is hit.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import jsonschema

from .context import CallerContext
from .costs import Usage, estimate_cost_usd
from .tools import HANDLERS, TOOL_SPECS, ToolError

log = logging.getLogger("tidewater.ask")

SYSTEM_PROMPT = (
    "You are Tidewater Ask, the support assistant for Tidewater Analytics customers. "
    "Answer questions about the caller's own shipments using the tools. Never guess a status. "
    "If you cannot help, open a ticket."
)

MAX_ROUNDS_ANSWER = "Sorry, I could not finish that request. Please try again or contact support."

_SCHEMAS = {s["toolSpec"]["name"]: s["toolSpec"]["inputSchema"]["json"] for s in TOOL_SPECS}


@dataclass
class TurnResult:
    outcome: str                 # "answered" | "blocked" | "max_rounds" | "truncated"
    answer: str                  # final text shown to the user
    messages: list[dict]         # the full conversation sent to / received from Bedrock
    usage: Usage
    cost_usd: float
    tool_calls: list[dict] = field(default_factory=list)   # [{"name", "status", "toolUseId"}]
    guardrail_action: str | None = None                    # trace action reason when blocked


def build_request(config: dict, messages: list[dict]) -> dict:
    """The keyword arguments for bedrock_runtime.converse()."""
    return {
        "modelId": config["model_id"],
        "system": [{"text": SYSTEM_PROMPT}],
        "messages": messages,
        "toolConfig": {"tools": TOOL_SPECS},
        "inferenceConfig": {"maxTokens": int(config["max_tokens"])},
        "guardrailConfig": {
            "guardrailIdentifier": config["guardrail"]["id"],
            "guardrailVersion": str(config["guardrail"]["version"]),
            "trace": "enabled",
        },
    }


def _text(message: dict) -> str:
    return "".join(b["text"] for b in message.get("content", []) if "text" in b).strip()


def _run_tool(table: Any, ctx: CallerContext, use: dict) -> tuple[dict, str]:
    name, tool_use_id = use["name"], use["toolUseId"]
    args = use.get("input") or {}

    def err(msg: str) -> tuple[dict, str]:
        return {"toolResult": {"toolUseId": tool_use_id, "content": [{"text": msg}], "status": "error"}}, "error"

    handler = HANDLERS.get(name)
    if handler is None:
        return err(f"Unknown tool {name!r}. Available tools: {', '.join(sorted(HANDLERS))}.")
    if isinstance(args, dict) and "tenant_id" in args:
        log.warning(json.dumps({"event": "ignored_tenant_arg", "request_id": ctx.request_id,
                                "tool": name, "tenant_id": ctx.tenant_id}))
    try:
        jsonschema.validate(args, _SCHEMAS[name])
    except jsonschema.ValidationError as e:
        return err(f"Invalid input for {name}: {e.message}")
    try:
        result = handler(table, ctx, args)
    except ToolError as e:
        return err(str(e))
    except Exception:  # noqa: BLE001 - never leak internals to the model
        log.exception("tool %s failed (request %s)", name, ctx.request_id)
        return err(f"{name} is temporarily unavailable. Do not retry it in this turn.")
    return {"toolResult": {"toolUseId": tool_use_id, "content": [{"json": result}], "status": "success"}}, "success"


def run_turn(client: Any, table: Any, ctx: CallerContext, question: str, config: dict) -> TurnResult:
    """Run one user turn."""
    messages: list[dict] = [{"role": "user", "content": [{"text": question}]}]
    usage = Usage()
    tool_calls: list[dict] = []
    rounds = 0
    max_rounds = int(config["max_tool_rounds"])

    def done(outcome: str, answer: str, action: str | None = None) -> TurnResult:
        cost = estimate_cost_usd(usage, config["model_id"], config["prices_per_1k"])
        return TurnResult(outcome, answer, messages, usage, cost, tool_calls, action)

    while True:
        resp = client.converse(**build_request(config, messages))
        usage.add(resp)
        stop = resp["stopReason"]
        message = resp["output"]["message"]
        log.info(json.dumps({
            "event": "model_call", "request_id": ctx.request_id, "tenant_id": ctx.tenant_id,
            "round": usage.model_calls, "stop_reason": stop,
            "input_tokens": usage.per_call[-1]["input_tokens"],
            "output_tokens": usage.per_call[-1]["output_tokens"],
            "latency_ms": usage.per_call[-1]["latency_ms"],
        }))

        if stop == "guardrail_intervened":
            messages.append(message)
            action = (resp.get("trace") or {}).get("guardrail", {}).get("actionReason") or "intervened"
            return done("blocked", _text(message), action)
        if stop == "max_tokens":
            messages.append(message)
            return done("truncated", _text(message))
        if stop == "tool_use":
            if rounds >= max_rounds:
                messages.append(message)
                return done("max_rounds", MAX_ROUNDS_ANSWER)
            messages.append(message)
            results = []
            for block in message["content"]:
                if "toolUse" in block:
                    result, status = _run_tool(table, ctx, block["toolUse"])
                    results.append(result)
                    tool_calls.append({"name": block["toolUse"]["name"], "status": status,
                                       "toolUseId": block["toolUse"]["toolUseId"]})
            messages.append({"role": "user", "content": results})
            rounds += 1
            continue
        messages.append(message)
        return done("answered", _text(message))
