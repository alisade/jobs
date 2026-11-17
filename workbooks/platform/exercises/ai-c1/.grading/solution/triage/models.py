"""The triage note contract: what the on-call engineer gets, validated before anyone sees it."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_use_id: str = Field(min_length=1, description="id of the tool call whose output supports this point")
    summary: str = Field(min_length=5)


class TriageNote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alert_id: str = Field(pattern=r"^ALR-[0-9]{4,6}$")
    severity: Literal["SEV1", "SEV2", "SEV3", "SEV4"]
    suspected_cause: str = Field(min_length=10, max_length=400)
    evidence: list[Evidence] = Field(min_length=1)
    next_steps: list[str] = Field(min_length=1)
    needs_human: bool

    @model_validator(mode="after")
    def high_severity_needs_a_human(self) -> "TriageNote":
        if self.severity in ("SEV1", "SEV2") and not self.needs_human:
            raise ValueError("SEV1/SEV2 notes must set needs_human: true")
        if any(not s.strip() for s in self.next_steps):
            raise ValueError("next_steps must not contain empty strings")
        return self
