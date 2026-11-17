"""Agent loop with read tools that run automatically and a write tool that needs confirmation.

Reference solution.
"""

from __future__ import annotations

import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .llm import LLMClient, Message
from .store import BackendError, NotFound, Store
from .tools import READ_TOOLS, SYSTEM_PROMPT, TOOLS, WRITE_TOOLS

MAX_TURNS = 6
MAX_TOOL_OUTPUT = 4000
ACTION_TTL_S = 300
TRUNCATED_NOTE = "\n[truncated: result too long]"
GAVE_UP = "I could not finish that request. A Kestrel teammate can help: use Talk to a person."


class ToolError(Exception):
    """An error the model should see as an is_error tool result."""


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

    # ---------- audit ----------
    def _audit(self, user_id: str, conversation_id: str, tool: str, args: Any, decision: str) -> None:
        self.audit.append({"user_id": user_id, "conversation_id": conversation_id, "tool": tool,
                           "args": args, "decision": decision, "at": self.clock()})

    # ---------- tools ----------
    def _own_order(self, user_id: str, order_id: str) -> dict:
        try:
            o = self.store.get_order(str(order_id))
        except NotFound:
            o = None
        if o is None or o["user_id"] != user_id:
            # same message for "missing" and "someone else's": do not leak that it exists
            raise ToolError(f"order {order_id} was not found for this customer")
        return o

    def _run_read(self, user_id: str, name: str, args: dict) -> Any:
        if name == "search_products":
            return {"results": self.store.search(str(args.get("query", "")))[:10]}
        if name == "check_inventory":
            try:
                n = self.store.check_inventory(str(args["sku"]), str(args["store_id"]))
            except NotFound as e:
                raise ToolError(str(e)) from e
            return {"sku": args["sku"], "store_id": args["store_id"], "available": n}
        if name == "get_order_status":
            o = self._own_order(user_id, args["order_id"])
            return {"order_id": o["order_id"], "status": o["status"], "items": o["items"],
                    "delivered_on": o["delivered_on"]}
        raise ToolError(f"unknown tool {name}")

    def _propose(self, user_id: str, conversation_id: str, name: str, args: dict) -> PendingAction:
        order_id = str(args.get("order_id", ""))
        reason = str(args.get("reason", ""))[:200]
        o = self._own_order(user_id, order_id)
        if o["status"] != "delivered":
            raise ToolError(f"order {order_id} is {o['status']}; only delivered orders can be returned")
        a = PendingAction(
            action_id="act_" + secrets.token_urlsafe(12), user_id=user_id, conversation_id=conversation_id,
            tool=name, args={"order_id": order_id, "reason": reason},  # extra keys such as confirmed are dropped
            summary=f"Start a return for order {order_id} ({', '.join(o['items'])}). Reason: {reason}",
            expires_at=self.clock() + ACTION_TTL_S,
        )
        self.actions[a.action_id] = a
        return a

    @staticmethod
    def _cap(s: str) -> str:
        if len(s) <= MAX_TOOL_OUTPUT:
            return s
        return s[: MAX_TOOL_OUTPUT - len(TRUNCATED_NOTE)] + TRUNCATED_NOTE

    # ---------- loop ----------
    def chat(self, user_id: str, conversation_id: str, message: str) -> TurnResult:
        msgs = self.conversations.setdefault(conversation_id, [])
        msgs.append({"role": "user", "content": message})
        pending: PendingAction | None = None
        for _ in range(MAX_TURNS):
            resp = self.llm.complete(SYSTEM_PROMPT, msgs, TOOLS)
            msgs.append({"role": "assistant", "content": resp.content})
            uses = [b for b in resp.content if b.get("type") == "tool_use"]
            if not uses:
                reply = "".join(b.get("text", "") for b in resp.content if b.get("type") == "text")
                return TurnResult(reply=reply, pending_action=pending)
            results = []
            for u in uses:
                name, args = u.get("name", ""), u.get("input") or {}
                is_error, decision = False, "executed"
                try:
                    if name in READ_TOOLS:
                        out = self._run_read(user_id, name, args)
                    elif name in WRITE_TOOLS:
                        if pending is not None:
                            raise ToolError("one change per turn: a confirmation is already waiting")
                        pending = self._propose(user_id, conversation_id, name, args)
                        decision = "pending"
                        out = {"status": "pending_confirmation", "action_id": pending.action_id,
                               "note": "Not started. The customer must confirm in the app."}
                    else:
                        raise ToolError(f"unknown tool {name}; available: {', '.join(t['name'] for t in TOOLS)}")
                    content = json.dumps(out)
                except ToolError as e:
                    is_error, decision, content = True, "denied" if name in READ_TOOLS | WRITE_TOOLS else "error", str(e)
                except (KeyError, TypeError) as e:
                    is_error, decision, content = True, "error", f"invalid input for {name}: missing {e}"
                except (BackendError, NotFound) as e:
                    is_error, decision, content = True, "error", f"{name} failed: {e}"
                self._audit(user_id, conversation_id, name, args, decision)
                results.append({"type": "tool_result", "tool_use_id": u.get("id"),
                                "content": self._cap(content), "is_error": is_error})
            msgs.append({"role": "user", "content": results})
        return TurnResult(reply=GAVE_UP, pending_action=pending, truncated=True)

    # ---------- confirmation ----------
    def confirm(self, user_id: str, conversation_id: str, action_id: str) -> dict:
        """Raises LookupError (404), PermissionError (403), TimeoutError (410), RuntimeError (409)."""
        a = self.actions.get(action_id)
        if a is None:
            raise LookupError(action_id)
        if a.user_id != user_id or a.conversation_id != conversation_id:
            self._audit(user_id, conversation_id, a.tool, a.args, "confirm_denied")
            raise PermissionError(action_id)
        if a.used:
            raise RuntimeError("already used")
        if self.clock() > a.expires_at:
            raise TimeoutError(action_id)
        a.used = True
        try:
            result = self.store.start_return(a.args["order_id"], a.args["reason"])
        except BackendError as e:
            self._audit(user_id, conversation_id, a.tool, a.args, "error")
            raise RuntimeError(str(e)) from e
        self._audit(user_id, conversation_id, a.tool, a.args, "confirmed")
        return result
