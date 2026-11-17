"""Authoring tool: run release 2026.44 (v1) on the time-skipping server, stop executions at
different points, and write their histories to histories/. Run from the exercise folder:
  BACKEND_TEMPORAL_TEST_SERVER=... ../../.venv/bin/python .grading/authoring/record_histories.py
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), ".grading", "authoring"))

from temporalio.testing import WorkflowEnvironment  # noqa: E402
from temporalio.worker import Worker  # noqa: E402

from keystone_workflows.activities import LeadActivities  # noqa: E402
from keystone_workflows.models import TASK_QUEUE, Approval, Lead  # noqa: E402
from v1_workflow import LeadAssignmentV1  # noqa: E402


async def wait_state(h, states):
    for _ in range(400):
        st = await h.query("status")
        if (st["state"] if isinstance(st, dict) else st.state) in states:
            return
        await asyncio.sleep(0.05)
    raise TimeoutError(states)


async def main() -> None:
    env = await WorkflowEnvironment.start_time_skipping(test_server_existing_path=os.environ["BACKEND_TEMPORAL_TEST_SERVER"])
    leads = {
        "lead-7f3a21-awaiting": Lead("lead-7f3a21", "bu-emea", "emea", "Fjordline Logistics", "cto@fjordline.example", 2400),
        "lead-91c0de-awaiting": Lead("lead-91c0de", "bu-amer", "amer", "Bluegate Health", "it@bluegate.example", 380),
        "lead-c44e09-escalated": Lead("lead-c44e09", "bu-apac", "apac", "Kiwa Robotics", "ops@kiwa.example", 1200),
        "lead-0b77aa-approved": Lead("lead-0b77aa", "bu-emea", "emea", "Nordhavn Energy", "cio@nordhavn.example", 5100),
    }
    os.makedirs("histories", exist_ok=True)
    async with env:
        async with Worker(env.client, task_queue=TASK_QUEUE, workflows=[LeadAssignmentV1], activities=LeadActivities().all()):
            handles = {}
            for name, ld in leads.items():
                handles[name] = await env.client.start_workflow("LeadAssignment", ld, id=f"lead-assign-{ld.lead_id}", task_queue=TASK_QUEUE)
            for name, h in handles.items():
                await wait_state(h, ("awaiting_approval",))
            await handles["lead-0b77aa-approved"].signal("approve", Approval("usr-emea-mgr-lindqvist"))
            await asyncio.wait_for(handles["lead-0b77aa-approved"].result(), 20)
            # Only the APAC lead's timer should fire: approve the others first, then skip time.
            # (Signals for the two awaiting leads are sent after we save their histories.)
            for name in ("lead-7f3a21-awaiting", "lead-91c0de-awaiting"):
                hist = await handles[name].fetch_history()
                open(f"histories/{name}.json", "w").write(hist.to_json())
            await env.sleep(49 * 3600)
            await wait_state(handles["lead-c44e09-escalated"], ("escalated",))
            for name in ("lead-c44e09-escalated", "lead-0b77aa-approved"):
                hist = await handles[name].fetch_history()
                open(f"histories/{name}.json", "w").write(hist.to_json())
    print("wrote", sorted(os.listdir("histories")))


if __name__ == "__main__":
    asyncio.run(main())
