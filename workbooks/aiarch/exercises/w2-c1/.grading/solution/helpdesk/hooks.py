"""Guardrails that must not depend on the prompt: an audit trail, a delete_* block, a model-call budget."""
from __future__ import annotations

from strands.hooks import AfterToolCallEvent, BeforeModelCallEvent, BeforeToolCallEvent, HookProvider, HookRegistry

BLOCK_MESSAGE = "blocked by policy: delete_* tools need a human change request"


class BudgetExceeded(RuntimeError):
    pass


class AuditHook(HookProvider):
    """Appends one record per tool call to ``log``: agent, tool, input, status (ok|error|blocked)."""

    def __init__(self, log: list):
        self.log = log

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeToolCallEvent, self.before)
        registry.add_callback(AfterToolCallEvent, self.after)

    def before(self, event: BeforeToolCallEvent) -> None:
        name = event.tool_use["name"]
        if name.startswith("delete_"):
            event.cancel_tool = BLOCK_MESSAGE

    def after(self, event: AfterToolCallEvent) -> None:
        name = event.tool_use["name"]
        if name.startswith("delete_"):
            status = "blocked"
        else:
            status = "ok" if event.result.get("status") == "success" else "error"
        self.log.append({"agent": event.agent.name, "tool": name,
                         "input": dict(event.tool_use.get("input") or {}), "status": status})


class BudgetHook(HookProvider):
    """Raises BudgetExceeded when one agent would make more than ``max_model_calls`` model calls."""

    def __init__(self, max_model_calls: int):
        self.max = max_model_calls
        self.calls = 0

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeModelCallEvent, self.before_model)

    def before_model(self, event: BeforeModelCallEvent) -> None:
        self.calls += 1
        if self.calls > self.max:
            raise BudgetExceeded(f"{event.agent.name}: more than {self.max} model calls in one request")
