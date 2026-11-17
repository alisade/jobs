"""Output contract of the PA assistant (given)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Criterion(BaseModel):
    criterion_id: str
    met: bool
    citation: str = Field(min_length=1)   # policy section id
    quote: str = Field(min_length=1)      # text the model says supports the finding


class Output(BaseModel):
    outcome: Literal["approve", "deny", "pend"]
    confidence: float = Field(ge=0, le=1)
    route: Literal["auto", "review"]
    criteria: list[Criterion] = Field(min_length=1)
