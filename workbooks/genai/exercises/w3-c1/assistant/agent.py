"""Agent loop for the Kestrel shopping assistant.

Prototype: it runs every tool the model asks for, including start_return, with no checks. That is
exactly what security review rejected. See README.md for the rules you must implement.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .llm import LLMClient, Message
from .store import Store
from .tools import SYSTEM_PROMPT, TOOLS

MAX_TURNS = 6
MAX_TOOL_OUTPUT = 4000
ACTION_TTL_S = 300
TRUNCATED_NOTE = "\n[truncated: result too long]"
GAVE_UP = "I could not finish that request. A Kestrel teammate can help: use Talk to a person."


@dataclass
class PendingAction:
    action_id: str
    user_id: str
    conversation_id: str
    tool: str
    args: dict
    summary: str
    expires_at: float
    used: bool = False


@dataclass
class TurnResult:
    reply: str
    pending_action: PendingAction | None = None
    truncated: bool = False


@dataclass
class Agent:
    llm: LLMClient
    store: Store
    clock: Callable[[], float] = time.monotonic
    actions: dict[str, PendingAction] = field(default_factory=dict)
    audit: list[dict] = field(default_factory=list)
    conversations: dict[str, list[Message]] = field(default_factory=dict)

    def _run(self, name: str, args: dict) -> Any:
        if name == "search_products":
            return {"results": self.store.search(args["query"])}
        if name == "check_inventory":
            return {"available": self.store.check_inventory(args["sku"], args["store_id"])}
        if name == "get_order_status":
            return self.store.get_order(args["order_id"])
        if name == "start_return":
            return self.store.start_return(args["order_id"], args["reason"])
        raise KeyError(name)

    def chat(self, user_id: str, conversation_id: str, message: str) -> TurnResult:
        msgs = self.conversations.setdefault(conversation_id, [])
        msgs.append({"role": "user", "content": message})
        for _ in range(50):
            resp = self.llm.complete(SYSTEM_PROMPT, msgs, TOOLS)
            msgs.append({"role": "assistant", "content": resp.content})
            uses = [b for b in resp.content if b.get("type") == "tool_use"]
            if not uses:
                return TurnResult(reply="".join(b.get("text", "") for b in resp.content if b.get("type") == "text"))
            results = []
            for u in uses:
                out = self._run(u["name"], u["input"])
                results.append({"type": "tool_result", "tool_use_id": u["id"], "content": json.dumps(out), "is_error": False})
            msgs.append({"role": "user", "content": results})
        return TurnResult(reply="")

    def confirm(self, user_id: str, conversation_id: str, action_id: str) -> dict:
        # TODO: execute a pending action once, for its owner, before it expires
        raise NotImplementedError
