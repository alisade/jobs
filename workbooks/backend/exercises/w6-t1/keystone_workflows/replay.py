"""Replay recorded histories against the current workflow code, offline (no server needed).

    python -m keystone_workflows.replay histories/*.json

This is what a worker does when it picks up an in-flight execution after a deploy. Run it in CI
against histories exported from production before you ship workflow changes.
"""

from __future__ import annotations

import asyncio
import sys

from temporalio.client import WorkflowHistory
from temporalio.worker import Replayer

from .lead_workflow import LeadAssignment


async def replay_file(path: str) -> str | None:
    """Return None when the history replays cleanly, else the error text."""
    with open(path) as f:
        hist = WorkflowHistory.from_json(path.rsplit("/", 1)[-1].removesuffix(".json"), f.read())
    try:
        await Replayer(workflows=[LeadAssignment]).replay_workflow(hist)
        return None
    except Exception as e:  # noqa: BLE001 - report every failure
        return f"{type(e).__name__}: {e}"


async def main(paths: list[str]) -> int:
    bad = 0
    for p in paths:
        err = await replay_file(p)
        print(f"{'OK  ' if err is None else 'FAIL'} {p}" + ("" if err is None else f"\n     {err[:400]}"))
        bad += err is not None
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
