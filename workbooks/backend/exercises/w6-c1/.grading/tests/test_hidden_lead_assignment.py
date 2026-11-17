"""Hidden tests for backend/w6-c1."""

import pytest
from temporalio.client import WorkflowFailureError, WorkflowUpdateFailedError

from keystone_workflows.models import REGION_MANAGERS, REGION_QUEUES, SALES_OPS, TASK_QUEUE, ApproveInput, RejectInput
from keystone_workflows.testkit import bounded, lead, rig, wait_state
from keystone_workflows.workflow import LeadAssignment


async def start(r, ld):
    return await r.env.client.start_workflow(LeadAssignment.run, ld, id=f"lead-assign-{ld.lead_id}", task_queue=TASK_QUEUE)


async def test_reject_signal_ends_without_assignment():
    async with rig() as r, r.worker([LeadAssignment]):
        h = await start(r, lead())
        await wait_state(h, LeadAssignment.status, ("awaiting_approval",))
        await h.signal(LeadAssignment.reject, RejectInput(by=REGION_MANAGERS["emea"], reason="existing customer, route to CSM"))
        out = await bounded(h.result())
        assert out.outcome == "rejected"
        assert r.api.assignments == []


async def test_validator_rejects_non_manager_and_keeps_waiting():
    async with rig() as r, r.worker([LeadAssignment]):
        h = await start(r, lead(region="emea"))
        await wait_state(h, LeadAssignment.status, ("awaiting_approval",))
        with pytest.raises(WorkflowUpdateFailedError):
            await bounded(h.execute_update(LeadAssignment.approve, ApproveInput(approver_id=REGION_MANAGERS["amer"])))
        st = await h.query(LeadAssignment.status)
        assert st.state == "awaiting_approval" and r.api.assignments == []
        # a rejected update is not in history: the real manager can still approve
        await bounded(h.execute_update(LeadAssignment.approve, ApproveInput(approver_id=REGION_MANAGERS["emea"], owner_id="usr-emea-ent-rep-7")))
        out = await bounded(h.result())
        assert out.outcome == "assigned" and out.owner_id == "usr-emea-ent-rep-7"


async def test_escalates_after_48h_then_queues_after_72h():
    async with rig() as r, r.worker([LeadAssignment]):
        ld = lead(region="apac", tenant_id="bu-apac")
        h = await start(r, ld)
        out = await bounded(h.result())  # time skips while nothing is waiting on us
        events = (await h.fetch_history()).events
        elapsed = events[-1].event_time.ToDatetime() - events[0].event_time.ToDatetime()
        assert out.outcome == "queued" and out.owner_id == REGION_QUEUES["apac"]
        assert [n["to"] for n in r.notifier.sent] == [SALES_OPS], r.notifier.sent
        assert r.acts.calls.get("escalate") == 1
        assert 71.5 <= elapsed.total_seconds() / 3600 <= 73, elapsed
        assert len(r.api.assignments) == 1 and r.api.assignments[0]["owner_id"] == REGION_QUEUES["apac"]
        st = await h.query(LeadAssignment.status)
        assert st.escalated is True


async def test_approval_after_escalation_still_counts():
    async with rig() as r, r.worker([LeadAssignment]):
        h = await start(r, lead())
        await wait_state(h, LeadAssignment.status, ("awaiting_approval",))
        await r.env.sleep(49 * 3600)
        st = await wait_state(h, LeadAssignment.status, ("escalated",))
        assert st.escalated
        await bounded(h.execute_update(LeadAssignment.approve, ApproveInput(approver_id=REGION_MANAGERS["emea"])))
        out = await bounded(h.result())
        assert out.outcome == "assigned" and out.owner_id == "usr-emea-ent-rep-1"
        assert r.acts.calls.get("escalate") == 1


async def test_worker_replaced_mid_wait():
    async with rig() as r:
        async with r.worker([LeadAssignment], cache=False):
            h = await start(r, lead())
            await wait_state(h, LeadAssignment.status, ("awaiting_approval",))
        # first worker is gone (rollout); a new one picks the workflow up and replays its history
        async with r.worker([LeadAssignment], cache=False):
            await bounded(h.execute_update(LeadAssignment.approve, ApproveInput(approver_id=REGION_MANAGERS["emea"])))
            out = await bounded(h.result())
        assert out.outcome == "assigned"
        assert r.acts.calls["score_lead"] == 1 and r.acts.calls["propose_owner"] == 1


async def test_assign_is_idempotent_across_activity_retry():
    async with rig(fail_first_after_commit=True) as r, r.worker([LeadAssignment]):
        ld = lead()
        h = await start(r, ld)
        await wait_state(h, LeadAssignment.status, ("awaiting_approval",))
        await bounded(h.execute_update(LeadAssignment.approve, ApproveInput(approver_id=REGION_MANAGERS["emea"])))
        out = await bounded(h.result())
        assert r.api.calls >= 2, "the first assign call fails after commit, so the activity must retry"
        assert len(r.api.assignments) == 1, f"double assignment: {r.api.assignments}"
        key = r.api.assignments[0]["idempotency_key"]
        assert key and f"lead-assign-{ld.lead_id}" in key, f"key {key!r} should derive from the workflow id"
        assert out.assignment_id == r.api.assignments[0]["assignment_id"]


async def test_validation_error_is_not_retried():
    async with rig() as r, r.worker([LeadAssignment]):
        h = await start(r, lead(region="latam", tenant_id="bu-amer"))
        with pytest.raises(WorkflowFailureError):
            await bounded(h.result())
        assert r.acts.calls.get("propose_owner") == 1


async def test_duplicate_decision_rejected():
    async with rig() as r, r.worker([LeadAssignment]):
        h = await start(r, lead())
        await wait_state(h, LeadAssignment.status, ("awaiting_approval",))
        await h.signal(LeadAssignment.reject, RejectInput(by=REGION_MANAGERS["emea"], reason="duplicate lead"))
        await bounded(h.result())
        st = await h.query(LeadAssignment.status)
        assert st.state == "rejected" and r.api.assignments == []
