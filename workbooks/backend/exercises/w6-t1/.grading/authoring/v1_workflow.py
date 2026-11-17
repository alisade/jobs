"""Release 2026.44 of LeadAssignment (the code that wrote histories/*.json). Authoring only:
record_histories.py runs it on the time-skipping server and saves the histories."""

from __future__ import annotations

import asyncio
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from keystone_workflows.activities import LeadActivities
    from keystone_workflows.models import SALES_OPS, Approval, AssignInput, EscalationInput, Lead, ProposeInput, Status

OPTS = dict(start_to_close_timeout=timedelta(seconds=30))


@workflow.defn(name="LeadAssignment")
class LeadAssignmentV1:
    def __init__(self) -> None:
        self._status = Status(state="scoring")
        self._approval: Approval | None = None

    @workflow.run
    async def run(self, lead: Lead) -> str:
        score = await workflow.execute_activity_method(LeadActivities.score_lead, lead, **OPTS)
        owner = await workflow.execute_activity_method(LeadActivities.propose_owner, ProposeInput(lead=lead, score=score), **OPTS)
        self._status.proposed_owner = owner
        self._status.sla_deadline = workflow.now() + timedelta(hours=48)
        self._status.state = "awaiting_approval"
        try:
            await workflow.wait_condition(lambda: self._approval is not None, timeout=timedelta(hours=48))
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
