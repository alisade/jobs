"""Extract CM-03 evidence for one sampled change with Gemini (google-genai), validated by Pydantic.

See README task 2 for the required behaviour. The dataclasses and the first tool declaration are
given; build_config() and extract() are yours.
"""

from __future__ import annotations

import json  # noqa: F401
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from google.genai import types
from pydantic import ValidationError  # noqa: F401

from .contract import ChangeEvidence

MODEL = "gemini-3.8-flash"
ALLOWED_TOOLS = ("get_ticket_approvals", "get_pr_checks")

SYSTEM_INSTRUCTION = (
    "You extract audit evidence for control CM-03. "  # TODO: finish the instruction (README task 2)
)

TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="get_ticket_approvals",
        description="Return the approval records (approver, decision, timestamp with offset, comment) for a change ticket.",
        parameters_json_schema={
            "type": "object",
            "properties": {"change_id": {"type": "string", "description": "ticket id, e.g. CHG-104118"}},
            "required": ["change_id"],
        },
    ),
    # TODO: declare get_pr_checks(pr_number: int)
]


@dataclass
class Usage:
    calls: int = 0
    prompt_tokens: int = 0
    output_tokens: int = 0


@dataclass
class ExtractionResult:
    status: Literal["ok", "needs_review"]
    evidence: ChangeEvidence | None
    errors: list[str] = field(default_factory=list)
    attempts: int = 0  # format attempts: model answers that were not tool calls
    tool_calls: list[str] = field(default_factory=list)  # every tool name the model asked for, in order
    usage: Usage = field(default_factory=Usage)


def build_config() -> types.GenerateContentConfig:
    raise NotImplementedError("TODO: README task 2")


def extract(
    client: Any,
    sample: dict,
    tools: dict[str, Callable[..., Any]],
    *,
    model: str = MODEL,
    max_attempts: int = 3,
    max_tool_turns: int = 4,
) -> ExtractionResult:
    raise NotImplementedError("TODO: README task 2")
