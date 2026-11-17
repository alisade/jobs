"""Pydantic contracts for CM-03 (program change) testing.

ChangeEvidence is what the model extracts: facts with citations, never conclusions. The
attribute conclusions are computed in code (attributes.py) from these facts and the deploy record.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["ticket", "pr", "deploy_log"]
    locator: str = Field(min_length=1, description="where in the source, e.g. approvals[0] or checks.conclusion")
    quote: str = Field(min_length=1, description="verbatim text from the source that supports the fact")


class ChangeEvidence(BaseModel):
    """Facts extracted for one sampled production change. Every field is required (no defaults):
    a missing key must fail validation instead of silently becoming a passing value."""

    model_config = ConfigDict(extra="forbid")

    change_id: str = Field(pattern=r"^CHG-\d{6}$")
    pr_number: int = Field(gt=0)
    author: str = Field(min_length=1)
    approver: str | None = Field(description="identity that approved the change ticket; null when no approval exists")
    approval_at: AwareDatetime | None = Field(description="approval timestamp with its UTC offset; null when none")
    tests_passed: bool | None = Field(description="CI conclusion for the PR; null when not in the evidence")
    citations: list[Citation] = Field(min_length=1)


class DeployRecord(BaseModel):
    """Row from the deployment pipeline log (system of record, not model output)."""

    model_config = ConfigDict(extra="ignore")

    change_id: str
    pr_number: int
    environment: str
    deployed_at: AwareDatetime
    pipeline_run: str


AttributeName = Literal["approval_before_deploy", "independent_approver", "linked_change", "tests_passed"]
Outcome = Literal["pass", "exception", "not_evaluable"]


class AttributeResult(BaseModel):
    attribute: AttributeName
    result: Outcome
    detail: str


def utc(ts: datetime) -> datetime:
    from datetime import timezone

    return ts.astimezone(timezone.utc)
