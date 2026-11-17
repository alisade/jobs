"""Test rig on the Temporal time-skipping test server (downloaded once by make setup). Provided."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from .activities import LeadActivities
from .models import TASK_QUEUE, Lead


def server_path() -> str:
    path = os.environ.get("BACKEND_TEMPORAL_TEST_SERVER", "")
    if not path or not os.path.exists(path):
        raise RuntimeError("BACKEND_TEMPORAL_TEST_SERVER is not set: run make setup, then make test")
    return path


@asynccontextmanager
async def env() -> AsyncIterator[WorkflowEnvironment]:
    e = await WorkflowEnvironment.start_time_skipping(test_server_existing_path=server_path())
    try:
        yield e
    finally:
        await e.shutdown()


def worker(e: WorkflowEnvironment, workflows: list, acts: LeadActivities, cache: bool = True) -> Worker:
    """cache=False: no workflow state kept in memory, every task (and query) replays the history."""
    extra = {} if cache else {"max_cached_workflows": 0}
    return Worker(e.client, task_queue=TASK_QUEUE, workflows=workflows, activities=acts.all(), **extra)


def new_lead(lead_id: str = "lead-55aa01") -> Lead:
    return Lead(lead_id, "bu-emea", "emea", "Fjordline Logistics", "cto@fjordline.example", 2400)


async def wait_state(handle, states: tuple[str, ...], timeout: float = 15.0):
    async def poll():
        while True:
            st = await handle.query("status")
            state = st["state"] if isinstance(st, dict) else st.state
            if state in states:
                return st
            await asyncio.sleep(0.05)
    return await asyncio.wait_for(poll(), timeout)
