"""The answer contract the assistant must return. TODO: constraints (README "Answer contract")."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Action(str, Enum):
    none = "none"
    watch = "watch"
    inspect_next_window = "inspect_next_window"
    raise_draft_work_order = "raise_draft_work_order"  # a suggestion for the planner, not an action taken


class Answer(BaseModel):
    answer: str
    citations: list[str]
    confidence: float
    recommended_action: Action
