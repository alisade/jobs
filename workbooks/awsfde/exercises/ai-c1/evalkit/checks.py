"""Deterministic checks on one recorded agent run. Each returns None (pass) or a short failure reason."""

from __future__ import annotations

CHECKS = ("tool_selected", "forbidden_tool", "grounded", "tenant_isolation", "refusal", "budget")


def tool_selected(case: dict, run: dict) -> str | None:
    """TODO: see README."""
    raise NotImplementedError



def forbidden_tool(case: dict, run: dict) -> str | None:
    """TODO: see README."""
    raise NotImplementedError



def grounded(case: dict, run: dict) -> str | None:
    """TODO: see README."""
    raise NotImplementedError



def tenant_isolation(case: dict, run: dict) -> str | None:
    """TODO: see README."""
    raise NotImplementedError



def refusal(case: dict, run: dict) -> str | None:
    """TODO: see README."""
    raise NotImplementedError



def budget(case: dict, run: dict) -> str | None:
    """TODO: see README."""
    raise NotImplementedError



ALL = {"tool_selected": tool_selected, "forbidden_tool": forbidden_tool, "grounded": grounded,
       "tenant_isolation": tenant_isolation, "refusal": refusal, "budget": budget}
