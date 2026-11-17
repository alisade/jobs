"""LeadAssignment, release 2026.45 (deployed Tuesday 2026-11-10 14:05 UTC).

Changes in this release (PR #812, "lead enrichment + SLA deadline on status"):
  - enrich_lead activity runs before propose_owner so the proposal can use firmographics
  - status.sla_deadline shows when the 48 h approval window ends (for the manager inbox UI)
  - sandbox disabled on this workflow: it raised RestrictedWorkflowAccessError on datetime.now
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import LeadActivities
    from .models import SALES_OPS, Approval, AssignInput, EscalationInput, Lead, ProposeInput, Status

OPTS = dict(start_to_close_timeout=timedelta(seconds=30))
APPROVAL_WINDOW = timedelta(hours=48)


@workflow.defn(name="LeadAssignment", sandboxed=False)
class LeadAssignment:
    def __init__(self) -> None:
        self._status = Status(state="scoring")
        self._approval: Approval | None = None

    @workflow.run
    async def run(self, lead: Lead) -> str:
        score = await workflow.execute_activity_method(LeadActivities.score_lead, lead, **OPTS)
        firmo = await workflow.execute_activity_method(LeadActivities.enrich_lead, lead, **OPTS)
        owner = await workflow.execute_activity_method(
            LeadActivities.propose_owner, ProposeInput(lead=lead, score=score, firmographics=firmo), **OPTS)
        self._status.proposed_owner = owner
        self._status.sla_deadline = datetime.now(timezone.utc) + APPROVAL_WINDOW
        self._status.state = "awaiting_approval"
        try:
            await workflow.wait_condition(lambda: self._approval is not None, timeout=APPROVAL_WINDOW)
        except asyncio.TimeoutError:
            self._status.escalated = True
            self._status.state = "escalated"
            await workflow.execute_activity_method(LeadActivities.escalate, EscalationInput(lead.lead_id, SALES_OPS, owner), **OPTS)
            await workflow.wait_condition(lambda: self._approval is not None)
        await workflow.execute_activity_method(
            LeadActivities.assign_owner, AssignInput(lead.lead_id, owner, f"{workflow.info().workflow_id}:assign"), **OPTS)
        self._status.state = "assigned"
        return owner

    @workflow.signal
    def approve(self, a: Approval) -> None:
        self._approval = a

    @workflow.query
    def status(self) -> Status:
        return self._status
