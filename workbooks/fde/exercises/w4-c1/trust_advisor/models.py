"""Structured outputs of the trust-advisor tools. Given; do not change: the tests and the
merchant-facing docs are written against these shapes."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ReasonExplanation(BaseModel):
    code: str
    meaning: str
    merchant_action: str


class DecisionExplanation(BaseModel):
    """One decision, safe to show a merchant engineer: no raw session id, email, IP or card."""

    decision_id: str
    ts: str
    hook: str
    outcome: Literal["allow", "deny", "review", "fail_open", "fail_closed"]
    reason_codes: list[str]
    explanations: list[ReasonExplanation]
    latency_ms: int
    session_digest: str
    analyst_note: str = ""  # redacted


class PolicyFinding(BaseModel):
    severity: Literal["error", "warning"]
    path: str  # dotted, e.g. "checkout.on_failure"; "" for the document root
    code: str  # unknown_key | missing_section | invalid_value | yaml_boolean | checkout_fail_open | budget_high
    message: str


class PolicyReport(BaseModel):
    valid: bool  # True when there is no finding of severity "error"
    findings: list[PolicyFinding] = Field(default_factory=list)


class HookCoverage(BaseModel):
    hook: str
    defined_by: str  # "module.QualName" of the first class in the MRO that defines it
    covered: bool  # defined by a trust mixin placed in front of the concrete backend


class HooksReport(BaseModel):
    backend: str
    resolution_order: list[str]  # the MRO as "module.QualName", object excluded
    hooks: list[HookCoverage]
    missing: list[str]  # required hooks not covered
    misordered_mixins: list[str]  # mixins that sit behind the concrete backend in the MRO
    ok: bool  # no missing hook and no misordered mixin


class DecisionStats(BaseModel):
    window: int  # how many decisions were counted
    hook: str | None
    counts: dict[str, int]  # outcome -> count, only outcomes that occur
    fail_open_rate: float  # fail_open / window, 0.0 for an empty window
    p95_latency_ms: int  # nearest-rank p95; 0 for an empty window
