"""Tool definitions, input validation and execution with server-side policy.

TODO: everything in this file. The definitions below are what the previous developer shipped;
the model keeps picking the wrong tool and inventing arguments. Rewrite them (see README,
"Tool design requirements"), then implement validate_input and execute_tool.
"""
from __future__ import annotations

from typing import Any

from parts_agent.backend import BackendError  # noqa: F401  (you will need it)
from parts_agent.session import Session

TOOLS: list[dict] = [
    {"name": "search", "description": "Searches.",
     "input_schema": {"type": "object", "properties": {"q": {"type": "string"}}}},
    {"name": "quote", "description": "Gets a quote.",
     "input_schema": {"type": "object", "properties": {"part": {"type": "string"}, "qty": {"type": "number"}}}},
    {"name": "doOrder", "description": "Orders a part.",
     "input_schema": {"type": "object", "properties": {"part": {"type": "string"}, "qty": {"type": "number"}}}},
]


def validate_input(schema: dict, data: Any, path: str = "") -> list[str]:
    """Validate data against the JSON-schema subset in README. Return a list of error strings,
    each starting with the property path (e.g. "quantity: must be <= 100"); [] when valid."""
    # TODO
    raise NotImplementedError


def execute_tool(session: Session, name: str, tool_input: Any) -> tuple[dict, bool]:
    """Run one tool call and return (result_dict, is_error). Must never raise."""
    # TODO
    raise NotImplementedError
