"""Hidden tests for backend/w6-t1."""

import asyncio
import glob
import re
from datetime import timedelta
from pathlib import Path

import pytest
from temporalio import workflow

from keystone_workflows.activities import LeadActivities
from keystone_workflows.lead_workflow import LeadAssignment
from keystone_workflows.models import TASK_QUEUE, Approval
from keystone_workflows.replay import replay_file
from keystone_workflows.testkit import env, new_lead, wait_state, worker

HISTORIES = sorted(glob.glob("histories/*.json"))


def test_histories_present():
    assert len(HISTORIES) == 4


@pytest.mark.parametrize("path", HISTORIES, ids=[Path(p).stem for p in HISTORIES])
async def test_history_replays_cleanly(path):
    err = await replay_file(path)
    assert err is None, err[:300]


async def test_new_execution_takes_new_path_with_marker():
    acts = LeadActivities()
    async with env() as e, worker(e, [LeadAssignment], acts):
        ld = new_lead("lead-new-001")
        h = await e.client.start_workflow(LeadAssignment.run, ld, id=f"lead-assign-{ld.lead_id}", task_queue=TASK_QUEUE)
        await wait_state(h, ("awaiting_approval",))
        await h.signal(LeadAssignment.approve, Approval("usr-emea-mgr-lindqvist"))
        await asyncio.wait_for(h.result(), 20)
        events = (await h.fetch_history()).events
        markers = [ev for ev in events if ev.HasField("marker_recorded_event_attributes")]
        assert markers, "new executions should record a version marker (workflow.patched) before the new activity"
        assert acts.calls.get("enrich_lead") == 1


async def test_sla_deadline_is_stable_across_replays():
    acts = LeadActivities()
    async with env() as e, worker(e, [LeadAssignment], acts, cache=False):
        ld = new_lead("lead-sla-001")
        h = await e.client.start_workflow(LeadAssignment.run, ld, id=f"lead-assign-{ld.lead_id}", task_queue=TASK_QUEUE)
        first = await wait_state(h, ("awaiting_approval",))
        await asyncio.sleep(1.2)
        await e.sleep(3 * 3600)
        second = await wait_state(h, ("awaiting_approval",))
        events = (await h.fetch_history()).events
        started = events[0].event_time.ToDatetime()
        d1, d2 = str(first["sla_deadline"]), str(second["sla_deadline"])
        assert d1 == d2, f"sla_deadline moved between replays: {d1} then {d2}"
        # deadline = workflow time when the proposal was made + 48 h, close to start + 48 h
        m = re.match(r"(\d{4}-\d\d-\d\dT\d\d:\d\d)", d1)
        assert m, d1
        expected = (started + timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M")
        assert m.group(1) == expected, f"deadline {d1} is not start + 48 h ({expected})"


def test_workflow_runs_in_the_sandbox():
    d = workflow._Definition.must_from_class(LeadAssignment)
    assert d.sandboxed, "the workflow sandbox is still disabled"


def test_answer_names_the_root_cause():
    text = Path("ANSWER.md").read_text().lower()
    assert re.search(r"non-?determinis", text), "ANSWER.md should name the nondeterminism"
    assert re.search(r"patch", text), "ANSWER.md should describe the patch / versioning fix"
