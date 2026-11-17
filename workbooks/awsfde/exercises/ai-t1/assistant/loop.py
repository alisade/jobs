"""The scheduled-report agent loop (Converse shapes). Runs unattended every Monday 07:00 UTC."""

from __future__ import annotations

import json
import logging
from typing import Any

from .context import JobContext
from .tools import TOOL_SPECS, Tools

log = logging.getLogger("tidewater.agent")
MAX_ROUNDS = 6


def run_job(model: Any, tools: Tools, ctx: JobContext, guardrail: dict) -> list[dict]:
    messages = [{"role": "user", "content": [{"text": ctx.task}]}]
    for _ in range(MAX_ROUNDS):
        resp = model.converse(modelId="us.anthropic.claude-sonnet-4-5-20250929-v1:0", messages=messages,
                              toolConfig={"tools": TOOL_SPECS},
                              guardrailConfig={"guardrailIdentifier": guardrail["id"], "guardrailVersion": guardrail["version"],
                                               "trace": "enabled"})
        msg = resp["output"]["message"]
        messages.append(msg)
        uses = [b["toolUse"] for b in msg["content"] if "toolUse" in b]
        log.info(json.dumps({"event": "model_call", "run_id": ctx.run_id, "stop_reason": resp["stopReason"],
                             "tool_uses": [u["name"] for u in uses], "guardrail_version": guardrail["version"],
                             "guardrail_action": resp.get("trace", {}).get("guardrail", {}).get("action")}))
        if resp["stopReason"] != "tool_use":
            break
        results = []
        for u in uses:
            content, status = tools.run(ctx, u["name"], u["input"])
            log.info(json.dumps({"event": "tool_call", "run_id": ctx.run_id, "tool": u["name"], "args": u["input"], "status": status}))
            results.append({"toolResult": {"toolUseId": u["toolUseId"], "content": [content], "status": status}})
        messages.append({"role": "user", "content": results})
    return messages
