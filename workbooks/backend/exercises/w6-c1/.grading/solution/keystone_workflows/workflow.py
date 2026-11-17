"""LeadAssignment: score, propose, wait for a manager decision, escalate, assign.

Workflow code is replayed from history after a crash, so it must be deterministic: no I/O, no
wall clock, no random. Every side effect is an activity.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .activities import LeadActivities
    from .models import (
        REGION_MANAGERS,
        REGION_QUEUES,
        SALES_OPS,
        ApproveInput,
        AssignInput,
        EscalationInput,
        Lead,
        Outcome,
        ProposeInput,
        RejectInput,
        Status,
    )

APPROVAL_WINDOW = timedelta(hours=48)
ESCALATION_WINDOW = timedelta(hours=24)

QUICK = dict(
    start_to_close_timeout=timedelta(seconds=10),
    retry_policy=RetryPolicy(initial_interval=timedelta(seconds=1), maximum_attempts=5,
                             non_retryable_error_types=["ValidationError"]),
)


@workflow.defn
class LeadAssignment:
    def __init__(self) -> None:
        self._lead: Lead | None = None
        self._status = Status(state="scoring")
        self._approval: ApproveInput | None = None
        self._rejection: RejectInput | None = None

    @workflow.run
    async def run(self, lead: Lead) -> Outcome:
        self._lead = lead
        score = await workflow.execute_activity_method(LeadActivities.score_lead, lead, **QUICK)
        proposed = await workflow.execute_activity_method(
            LeadActivities.propose_owner, ProposeInput(lead=lead, score=score), **QUICK)
        self._status.proposed_owner = proposed
        self._status.state = "awaiting_approval"

        if not await self._wait_for_decision(APPROVAL_WINDOW):
            self._status.escalated = True
            self._status.state = "escalated"
            await workflow.execute_activity_method(
                LeadActivities.escalate,
                EscalationInput(lead_id=lead.lead_id, region=lead.region, to=SALES_OPS,
                                proposed_owner=proposed, waited_hours=48),
                **QUICK)
            if not await self._wait_for_decision(ESCALATION_WINDOW):
                queue = REGION_QUEUES[lead.region]
                asg = await self._assign(lead, queue)
                self._status.state = "queued"
                return Outcome(outcome="queued", owner_id=queue, assignment_id=asg,
                               notes=["no decision in 72 h"])

        if self._rejection is not None:
            self._status.state = "rejected"
            self._status.decided_by = self._rejection.by
            return Outcome(outcome="rejected", decided_by=self._rejection.by, notes=[self._rejection.reason])

        assert self._approval is not None
        owner = self._approval.owner_id or proposed
        asg = await self._assign(lead, owner)
        self._status.state = "assigned"
        return Outcome(outcome="assigned", owner_id=owner, assignment_id=asg, decided_by=self._approval.approver_id)

    async def _wait_for_decision(self, window: timedelta) -> bool:
        try:
            await workflow.wait_condition(lambda: self._approval is not None or self._rejection is not None,
                                          timeout=window)
            return True
        except asyncio.TimeoutError:
            return False

    async def _assign(self, lead: Lead, owner: str) -> str:
        self._status.state = "assigning"
        # Stable across activity retries and worker restarts: derived from the workflow id, not a uuid.
        key = f"{workflow.info().workflow_id}:assign"
        asg = await workflow.execute_activity_method(
            LeadActivities.assign_owner,
            AssignInput(lead_id=lead.lead_id, tenant_id=lead.tenant_id, owner_id=owner, idempotency_key=key),
            **QUICK)
        self._status.assigned_owner = owner
        return asg

    @workflow.update
    async def approve(self, inp: ApproveInput) -> str:
        self._approval = inp
        self._status.decided_by = inp.approver_id
        return "approved"

    @approve.validator
    def _validate_approve(self, inp: ApproveInput) -> None:
        if self._lead is None or self._status.state not in ("awaiting_approval", "escalated"):
            raise ValueError(f"lead is not awaiting approval (state={self._status.state})")
        if self._approval is not None or self._rejection is not None:
            raise ValueError("a decision was already recorded")
        manager = REGION_MANAGERS.get(self._lead.region)
        if inp.approver_id != manager:
            raise ValueError(f"{inp.approver_id} is not the {self._lead.region} region manager")

    @workflow.signal
    def reject(self, inp: RejectInput) -> None:
        if self._approval is None and self._rejection is None:
            self._rejection = inp

    @workflow.query
    def status(self) -> Status:
        return self._status
