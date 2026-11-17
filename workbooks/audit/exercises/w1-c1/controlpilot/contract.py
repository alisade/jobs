"""Pydantic contracts for CM-03 (program change) testing.

ChangeEvidence is what the model extracts: facts with citations, never conclusions. The
attribute conclusions are computed in code (attributes.py) from these facts and the deploy record.

TODO (README task 1): this draft is too lenient to be an audit contract. Tighten it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Citation(BaseModel):
    source: str
    locator: str
    quote: str


class ChangeEvidence(BaseModel):
    """Facts extracted for one sampled production change."""

    change_id: str
    pr_number: int
    author: str
    approver: str = ""
    approval_at: datetime | None = None
    tests_passed: bool = True
    citations: list[Citation] = []


class DeployRecord(BaseModel):
    """Row from the deployment pipeline log (system of record, not model output). Complete."""

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
    return ts.astimezone(timezone.utc)
