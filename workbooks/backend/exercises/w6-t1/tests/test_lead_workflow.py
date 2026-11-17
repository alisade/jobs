"""Visible tests. The first passes today; the second is the incident."""

import asyncio
import glob

from keystone_workflows.activities import LeadActivities
from keystone_workflows.lead_workflow import LeadAssignment
from keystone_workflows.models import TASK_QUEUE, Approval
from keystone_workflows.replay import replay_file
from keystone_workflows.testkit import env, new_lead, wait_state, worker


async def test_new_execution_enriches_and_assigns():
    acts = LeadActivities()
    async with env() as e, worker(e, [LeadAssignment], acts):
        ld = new_lead()
        h = await e.client.start_workflow(LeadAssignment.run, ld, id=f"lead-assign-{ld.lead_id}", task_queue=TASK_QUEUE)
        await wait_state(h, ("awaiting_approval",))
        await h.signal(LeadAssignment.approve, Approval("usr-emea-mgr-lindqvist"))
        assert await asyncio.wait_for(h.result(), 20) == "usr-emea-ent-rep-1"
        assert acts.calls.get("enrich_lead") == 1


async def test_recorded_histories_replay():
    failures = {}
    for path in sorted(glob.glob("histories/*.json")):
        err = await replay_file(path)
        if err:
            failures[path] = err[:200]
    assert not failures, failures
