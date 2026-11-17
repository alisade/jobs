"""Tools for the nightly CM-03 tester."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from google.adk.tools import ToolContext

from . import queue

log = logging.getLogger("nightly.tools")

SAMPLE = [f"CHG-10{n}" for n in range(5101, 5111)]       # Q3 CM-03 sample, 10 changes
EXCEPTIONS = {"CHG-105103", "CHG-105107", "CHG-105109"}  # what the test finds (simulated)
BATCH_SIZE = 5

# Progress tracking. temp: keys are per-run scratch space, so a fresh run starts clean
# and we never carry stale progress from yesterday's crashed run.
COMPLETED_KEY = "temp:completed"


def _db() -> Path:
    return Path(os.environ.get("NIGHTLY_RUN_DIR", "run")) / "queue.db"


def next_batch(tool_context: ToolContext) -> dict:
    """Return the next change ids in the sample that have not been tested yet (at most 5)."""
    done = set(tool_context.state.get(COMPLETED_KEY, []))
    todo = [c for c in SAMPLE if c not in done][:BATCH_SIZE]
    log.info("next_batch: %d done, returning %s", len(done), todo)
    return {"change_ids": todo}


def test_change(change_id: str, tool_context: ToolContext) -> dict:
    """Test one sampled change against CM-03 and open a review work item for an exception."""
    if change_id == "CHG-105104":
        log.warning("GRC API 429 Too Many Requests for %s, retrying in 2s (attempt 1/5)", change_id)
        log.info("GRC API retry succeeded for %s", change_id)
    db = queue.connect(_db())
    db.execute("INSERT INTO tested VALUES (?, ?)", (change_id, tool_context.invocation_id))
    result = "exception" if change_id in EXCEPTIONS else "pass"
    if result == "exception":
        db.execute("INSERT INTO work_items (change_id, kind, created_by) VALUES (?, 'cm03-exception-review', 'controlpilot')", (change_id,))
    db.commit()
    done = list(tool_context.state.get(COMPLETED_KEY, []))
    if change_id not in done:
        done.append(change_id)
    tool_context.state[COMPLETED_KEY] = done
    return {"change_id": change_id, "result": result}
