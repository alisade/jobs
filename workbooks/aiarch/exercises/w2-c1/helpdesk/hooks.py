"""Guardrails that must not depend on the prompt.

TODO:
- AuditHook: one record per tool call appended to ``log``:
  {"agent": <agent name>, "tool": <tool name>, "input": <dict>, "status": "ok" | "error" | "blocked"}
  and cancel any tool whose name starts with "delete_" with BLOCK_MESSAGE.
- BudgetHook: raise BudgetExceeded when one agent would make more than max_model_calls model calls.
Hint: strands.hooks has BeforeToolCallEvent, AfterToolCallEvent and BeforeModelCallEvent.
"""
from __future__ import annotations

from strands.hooks import HookProvider, HookRegistry

BLOCK_MESSAGE = "blocked by policy: delete_* tools need a human change request"


class BudgetExceeded(RuntimeError):
    pass


class AuditHook(HookProvider):
    def __init__(self, log: list):
        self.log = log

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        pass  # TODO


class BudgetHook(HookProvider):
    def __init__(self, max_model_calls: int):
        self.max = max_model_calls

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        pass  # TODO
