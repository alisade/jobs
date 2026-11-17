"""Test rig: a Temporal time-skipping test server (downloaded once into backend/.temporal by
make setup), a worker with the fake activities, and helpers with bounded waits. Provided."""

from __future__ import annotations

import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from .activities import FakeAccountsApi, LeadActivities, Notifier
from .models import TASK_QUEUE, Lead


def server_path() -> str:
    path = os.environ.get("BACKEND_TEMPORAL_TEST_SERVER", "")
    if not path or not os.path.exists(path):
        raise RuntimeError("BACKEND_TEMPORAL_TEST_SERVER is not set: run make setup, then make test "
                           "(the Makefile exports it from backend/_env/ensure-temporal.sh)")
    return path


@dataclass
class Rig:
    env: WorkflowEnvironment
    api: FakeAccountsApi
    notifier: Notifier
    acts: LeadActivities

    def worker(self, workflows: list, cache: bool = True) -> Worker:
        """cache=False keeps no workflow state in memory, so every workflow task is a full replay
        from history, as on a freshly started pod."""
        extra = {} if cache else {"max_cached_workflows": 0}
        return Worker(self.env.client, task_queue=TASK_QUEUE, workflows=workflows, activities=self.acts.all(), **extra)


@asynccontextmanager
async def rig(fail_first_after_commit: bool = False) -> AsyncIterator[Rig]:
    env = await WorkflowEnvironment.start_time_skipping(test_server_existing_path=server_path())
    api = FakeAccountsApi(fail_first_after_commit=fail_first_after_commit)
    notifier = Notifier()
    try:
        yield Rig(env=env, api=api, notifier=notifier, acts=LeadActivities(api, notifier))
    finally:
        await env.shutdown()


def lead(region: str = "emea", employees: int = 2400, **kw) -> Lead:
    base = dict(lead_id=f"lead-{uuid.uuid4().hex[:8]}", tenant_id="bu-emea", region=region,
                company="Fjordline Logistics", email="cto@fjordline.example", employees=employees)
    base.update(kw)
    return Lead(**base)


async def wait_state(handle, query, states: tuple[str, ...], timeout: float = 15.0):
    """Poll the status query until the workflow reaches one of states (bounded)."""
    async def poll():
        while True:
            st = await handle.query(query)
            if st.state in states:
                return st
            await asyncio.sleep(0.05)
    return await asyncio.wait_for(poll(), timeout)


async def bounded(coro, timeout: float = 20.0):
    return await asyncio.wait_for(coro, timeout)
