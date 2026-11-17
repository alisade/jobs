"""Orchestrator plus two specialists as tools (the agents-as-tools pattern)."""
from __future__ import annotations

from typing import Callable

from strands import Agent, tool
from strands.models.model import Model

from .hooks import AuditHook, BudgetHook
from .store import Store
from .tools import it_tools, review_tools

ORCHESTRATOR_PROMPT = ("You route Harbor Point employees' requests. Use it_requests for laptops, software, "
                       "network and tickets; access_reviews for pending access reviews. Answer briefly.")
IT_PROMPT = "You handle IT tickets. Use the tools; never invent ticket numbers."
REVIEW_PROMPT = "You report pending access reviews for a team. You cannot approve or delete reviews."


def build_orchestrator(model_factory: Callable[[str], Model], store: Store, requester: str,
                       audit_log: list, max_model_calls: int = 8) -> Agent:
    def specialist(name: str, prompt: str, tools: list) -> Agent:
        return Agent(name=name, model=model_factory(name), system_prompt=prompt, tools=tools,
                     hooks=[AuditHook(audit_log), BudgetHook(max_model_calls)], callback_handler=None)

    @tool
    def it_requests(query: str) -> str:
        """Hand an IT request (tickets, laptops, software, network) to the IT specialist."""
        agent = specialist("it_requests", IT_PROMPT, it_tools(store, requester))
        return str(agent(query)).strip()

    @tool
    def access_reviews(query: str) -> str:
        """Hand an access-review question (pending reviews for a team) to the access-review specialist."""
        agent = specialist("access_reviews", REVIEW_PROMPT, review_tools(store, requester))
        return str(agent(query)).strip()

    return Agent(name="orchestrator", model=model_factory("orchestrator"), system_prompt=ORCHESTRATOR_PROMPT,
                 tools=[it_requests, access_reviews],
                 hooks=[AuditHook(audit_log), BudgetHook(max_model_calls)], callback_handler=None)
