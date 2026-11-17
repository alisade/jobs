"""Build and run the ADK CM-03 tester for one sample. See README tasks 3-4."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from google.adk import Agent, Runner  # noqa: F401
from google.adk.sessions import InMemorySessionService  # noqa: F401
from google.genai import types  # noqa: F401
from pydantic import BaseModel, ConfigDict, ValidationError  # noqa: F401

from . import systems
from .guard import make_after_tool, make_before_tool  # noqa: F401

INSTRUCTION = """You test control CM-03 (program change) for Meridian Freight Holdings internal audit.
Call list_sample first. For each sampled change, read the ticket, the PR and the deploy record, then
call record_result once. When every sampled change is recorded, answer with one JSON object:
{"control": "CM-03", "results": [{"change_id": ..., "result": "pass" | "exception" | "needs_review",
"failed_attributes": [...]}]}."""


class ResultRow(BaseModel):
    change_id: str
    result: str
    failed_attributes: list[str] = []


class TestSummary(BaseModel):
    control: str
    results: list[ResultRow]


@dataclass
class RunOutcome:
    status: Literal["ok", "needs_review"]
    summary: TestSummary | None
    results: dict          # what record_result stored in session state, by change id
    log: list[dict]        # the execution log
    problems: list[str] = field(default_factory=list)


def build_agent(llm, sample_ids: list[str], log: list[dict], max_tool_calls: int = 16):
    # Draft: every tool in the shared registry, no callbacks.
    from google.adk import Agent
    return Agent(name="cm03_tester", model=llm, instruction=INSTRUCTION, tools=list(systems.TOOL_REGISTRY.values()))


def check_summary(text: str, recorded: dict, sample_ids: list[str]) -> tuple[TestSummary | None, list[str]]:
    raise NotImplementedError("TODO: README task 4")


async def run_test(llm, sample_ids: list[str], *, max_tool_calls: int = 16) -> RunOutcome:
    raise NotImplementedError("TODO: README task 3")
