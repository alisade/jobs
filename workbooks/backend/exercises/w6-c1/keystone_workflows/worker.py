"""Run a worker against a local Temporal dev server (optional, not used by the tests):
    temporal server start-dev   # if you have the Temporal CLI
    python -m keystone_workflows.worker
"""

from __future__ import annotations

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from .activities import FakeAccountsApi, LeadActivities, Notifier
from .models import TASK_QUEUE
from .workflow import LeadAssignment


async def main() -> None:
    client = await Client.connect("localhost:7233")
    acts = LeadActivities(FakeAccountsApi(), Notifier())
    async with Worker(client, task_queue=TASK_QUEUE, workflows=[LeadAssignment], activities=acts.all()):
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
