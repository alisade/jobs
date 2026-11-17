"""LeadAssignment: score, propose, wait for a manager decision, escalate, assign.

Workflow code is replayed from history after a crash, so it must be deterministic: no I/O, no
wall clock, no random. Every side effect is an activity.

This is the spike from the design review. It runs the happy path once on a good day. Your job
is to turn it into the primitive product teams and agents will call (see README requirements).
"""

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import LeadActivities
    from .models import (  # noqa: F401  (you will need most of these)
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


@workflow.defn
class LeadAssignment:
    def __init__(self) -> None:
        self._lead: Lead | None = None
        self._status = Status(state="scoring")
        self._approval: ApproveInput | None = None

    @workflow.run
    async def run(self, lead: Lead) -> Outcome:
        self._lead = lead
        score = await workflow.execute_activity_method(
            LeadActivities.score_lead, lead, start_to_close_timeout=timedelta(seconds=10))
        proposed = await workflow.execute_activity_method(
            LeadActivities.propose_owner, ProposeInput(lead=lead, score=score),
            start_to_close_timeout=timedelta(seconds=10))
        self._status.proposed_owner = proposed
        self._status.state = "awaiting_approval"

        # TODO: wait at most 48 h, then escalate to sales ops, then 24 h more, then the region queue.
        # TODO: a reject signal ends the workflow without an assignment.
        await workflow.wait_condition(lambda: self._approval is not None)

        owner = self._approval.owner_id or proposed
        # TODO: retry policy (non-retryable ValidationError) and an idempotency key that survives
        # activity retries and worker restarts.
        asg = await workflow.execute_activity_method(
            LeadActivities.assign_owner,
            AssignInput(lead_id=lead.lead_id, tenant_id=lead.tenant_id, owner_id=owner, idempotency_key=""),
            start_to_close_timeout=timedelta(seconds=10))
        self._status.state = "assigned"
        self._status.assigned_owner = owner
        return Outcome(outcome="assigned", owner_id=owner, assignment_id=asg, decided_by=self._approval.approver_id)

    @workflow.update
    async def approve(self, inp: ApproveInput) -> str:
        # TODO: a validator that rejects anyone but the lead's region manager, and late or
        # duplicate decisions, before the update is written to history.
        self._approval = inp
        return "approved"

    # TODO: @workflow.signal reject(RejectInput)

    @workflow.query
    def status(self) -> Status:
        return self._status
