"""Visible tests: the happy path. The hidden tests cover the rest of the README."""

from keystone_workflows.models import REGION_MANAGERS, TASK_QUEUE, ApproveInput
from keystone_workflows.testkit import bounded, lead, rig, wait_state
from keystone_workflows.workflow import LeadAssignment


async def test_manager_approves_proposed_owner():
    async with rig() as r, r.worker([LeadAssignment]):
        ld = lead()
        h = await r.env.client.start_workflow(LeadAssignment.run, ld, id=f"lead-assign-{ld.lead_id}", task_queue=TASK_QUEUE)
        st = await wait_state(h, LeadAssignment.status, ("awaiting_approval",))
        assert st.proposed_owner == "usr-emea-ent-rep-1"
        await bounded(h.execute_update(LeadAssignment.approve, ApproveInput(approver_id=REGION_MANAGERS["emea"])))
        out = await bounded(h.result())
        assert out.outcome == "assigned" and out.owner_id == "usr-emea-ent-rep-1"
        assert len(r.api.assignments) == 1
