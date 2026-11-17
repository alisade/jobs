"""One assistant turn on Amazon Bedrock with the Converse API.

run_turn() sends the user's question, runs any tools the model asks for, sends the results
back, and repeats until the model answers, the guardrail intervenes, or the round limit is hit.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from .context import CallerContext
from .costs import Usage, estimate_cost_usd
from .tools import HANDLERS, TOOL_SPECS, ToolError

log = logging.getLogger("tidewater.ask")

SYSTEM_PROMPT = (
    "You are Tidewater Ask, the support assistant for Tidewater Analytics customers. "
    "Answer questions about the caller's own shipments using the tools. Never guess a status. "
    "If you cannot help, open a ticket."
)


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
    """The keyword arguments for bedrock_runtime.converse().

    TODO: modelId from config, the system prompt, the conversation, toolConfig with
    TOOL_SPECS, inferenceConfig.maxTokens from config, and guardrailConfig with the
    guardrail id and version from config and trace enabled.
    """
    raise NotImplementedError


def run_turn(client: Any, table: Any, ctx: CallerContext, question: str, config: dict) -> TurnResult:
    """Run one user turn.

    TODO (see README for the full contract):
    - start the conversation with the user's question
    - call converse; account usage; log one JSON line per model call
    - stopReason "tool_use": append the assistant message, run EVERY toolUse block, and send all
      results back in ONE user message (same order as the toolUse blocks)
    - tool handlers get the verified ctx; a "tenant_id" in the model's input is never used
    - stopReason "guardrail_intervened": outcome "blocked", no tools run
    - stopReason "max_tokens": outcome "truncated"
    - stop after config["max_tool_rounds"] tool rounds: outcome "max_rounds"
    """
    raise NotImplementedError
