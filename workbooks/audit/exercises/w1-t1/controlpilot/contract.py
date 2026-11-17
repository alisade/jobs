"""Result contract for one CM-03 sample."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChangeAssessment(BaseModel):
    # Forward compatible: ignore keys we do not know about so prompt tweaks never break a run.
    model_config = ConfigDict(extra="ignore")

    change_id: str
    pr_number: int
    author: str
    approver: str | None = None
    approval_at: datetime | None = None
    approved_before_deploy: bool = True
    independent_approver: bool = True
    tests_passed: bool = True
