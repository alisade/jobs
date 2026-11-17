"""The answer contract the assistant must return."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Action(str, Enum):
    none = "none"
    watch = "watch"
    inspect_next_window = "inspect_next_window"
    raise_draft_work_order = "raise_draft_work_order"  # a suggestion for the planner, not an action taken


class Answer(BaseModel):
    answer: str = Field(min_length=1, max_length=1200)
    citations: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    recommended_action: Action
