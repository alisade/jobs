"""Result contract for one CM-03 sample: facts only, every key required, unknown keys rejected."""

from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: Literal["ticket", "pr", "deploy_log"]
    locator: str = Field(min_length=1)
    quote: str = Field(min_length=1)


class ChangeFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    change_id: str = Field(pattern=r"^CHG-\d{6}$")
    pr_number: int = Field(gt=0)
    author: str = Field(min_length=1)
    approver: str | None
    approval_at: AwareDatetime | None
    tests_passed: bool | None
    citations: list[Citation] = Field(min_length=1)


# Kept so old imports still resolve; the model no longer reports conclusions.
ChangeAssessment = ChangeFacts
