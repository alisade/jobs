"""Typed inputs and outputs for the lead-assignment primitive (shared by workflow and activities)."""

from __future__ import annotations

from dataclasses import dataclass, field

TASK_QUEUE = "keystone-lead-assignment"

# Who may approve a proposed owner for a lead in each sales region (from the org chart sync).
REGION_MANAGERS: dict[str, str] = {
    "amer": "usr-amer-mgr-ortiz",
    "emea": "usr-emea-mgr-lindqvist",
    "apac": "usr-apac-mgr-tanaka",
}

# Where a lead goes when nobody decides in time: the region's shared queue (a pseudo-owner).
REGION_QUEUES: dict[str, str] = {r: f"queue-{r}-inbound" for r in REGION_MANAGERS}

SALES_OPS = "grp-sales-ops"


@dataclass
class Lead:
    lead_id: str
    tenant_id: str
    region: str
    company: str
    email: str
    employees: int = 0


@dataclass
class ProposeInput:
    lead: Lead
    score: int


@dataclass
class ApproveInput:
    approver_id: str
    owner_id: str | None = None  # the manager may pick a different owner than the proposal


@dataclass
class RejectInput:
    by: str
    reason: str


@dataclass
class EscalationInput:
    lead_id: str
    region: str
    to: str
    proposed_owner: str
    waited_hours: int


@dataclass
class AssignInput:
    lead_id: str
    tenant_id: str
    owner_id: str
    idempotency_key: str


@dataclass
class Status:
    state: str  # scoring | awaiting_approval | escalated | assigning | assigned | rejected | queued
    proposed_owner: str | None = None
    assigned_owner: str | None = None
    escalated: bool = False
    decided_by: str | None = None


@dataclass
class Outcome:
    outcome: str  # assigned | rejected | queued
    owner_id: str | None = None
    assignment_id: str | None = None
    decided_by: str | None = None
    notes: list[str] = field(default_factory=list)
