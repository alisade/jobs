"""Orchestrator plus two specialists as tools (the agents-as-tools pattern).

TODO: build_orchestrator must return an Agent named "orchestrator" whose only tools are
it_requests and access_reviews. Each of those runs a specialist Agent (named "it_requests" /
"access_reviews", model from model_factory(name), the tools from tools.py) and returns its final
text. Every agent gets AuditHook(audit_log) and BudgetHook(max_model_calls).
"""
from __future__ import annotations

from typing import Callable

from strands import Agent, tool
from strands.models.model import Model

from .store import Store


def build_orchestrator(model_factory: Callable[[str], Model], store: Store, requester: str,
                       audit_log: list, max_model_calls: int = 8) -> Agent:
    @tool
    def it_requests(query: str) -> str:
        """IT requests."""
        return "not implemented"  # TODO

    @tool
    def access_reviews(query: str) -> str:
        """Access reviews."""
        return "not implemented"  # TODO

    return Agent(name="orchestrator", model=model_factory("orchestrator"),
                 tools=[it_requests, access_reviews], callback_handler=None)
