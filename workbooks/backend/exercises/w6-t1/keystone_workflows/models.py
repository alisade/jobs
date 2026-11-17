"""Inputs, outputs and constants for the lead-assignment workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

TASK_QUEUE = "keystone-lead-assignment"
REGION_MANAGERS = {"amer": "usr-amer-mgr-ortiz", "emea": "usr-emea-mgr-lindqvist", "apac": "usr-apac-mgr-tanaka"}
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
    firmographics: dict | None = None  # added in 2026.45 (enrichment)


@dataclass
class Approval:
    approver_id: str


@dataclass
class EscalationInput:
    lead_id: str
    to: str
    proposed_owner: str


@dataclass
class AssignInput:
    lead_id: str
    owner_id: str
    idempotency_key: str


@dataclass
class Status:
    state: str
    proposed_owner: str | None = None
    sla_deadline: datetime | None = None
    escalated: bool = False
