"""Publish stage of a ControlPilot run: for every tested sample append the workpaper row to the
run's append blob, and raise a GRC issue for each confirmed exception. Checkpointed per sample."""

from __future__ import annotations

import json
from typing import Callable

from .grc_client import GrcClient, GrcUnavailable
from .store import Checkpoints


def run_publish(run_id: str, samples: list[dict], *, server, blob, store: Checkpoints,
                sleep: Callable[[float], None], log: Callable[[str], None], step_attempts: int = 3) -> dict:
    """samples: [{"sample_id", "conclusion" ("pass"|"exception"), "attributes": {...}}].
    Returns {"published": [...], "issues": {sample_id: issue_id}, "failed": [...]}."""
    client = GrcClient(server, sleep=sleep, log=log)
    out: dict = {"published": [], "issues": {}, "failed": []}
    for s in samples:
        sid = s["sample_id"]
        if store.get(run_id, sid, "published") is not None:
            log(f"run {run_id}: {sid} already published, skipping")
            out["published"].append(sid)
            continue
        for attempt in range(1, step_attempts + 1):
            try:
                row = {"run_id": run_id, "sample_id": sid, "control": "CM-03",
                       "conclusion": s["conclusion"], "attributes": s["attributes"]}
                blob.append_block(json.dumps(row, sort_keys=True) + "\n")
                issue_id = ""
                if s["conclusion"] == "exception":
                    payload = {"run_id": run_id, "sample_id": sid, "control": "CM-03",
                               "title": f"CM-03 exception {sid}", "attributes": s["attributes"]}
                    issue_id = client.create_issue(payload)
                    out["issues"][sid] = issue_id
                store.put(run_id, sid, "published", issue_id)
                out["published"].append(sid)
                log(f"run {run_id}: {sid} published (step attempt {attempt})")
                break
            except GrcUnavailable as e:
                log(f"run {run_id}: {sid} step attempt {attempt}/{step_attempts} failed: {e}; retrying step in 60s")
                sleep(60)
        else:
            out["failed"].append(sid)
    return out
