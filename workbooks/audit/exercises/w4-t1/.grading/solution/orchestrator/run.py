"""Publish stage of a ControlPilot run: for every tested sample append the workpaper row to the
run's append blob, and raise a GRC issue for each confirmed exception.

Each side effect is its own checkpointed step and is idempotent on its own:
  - workpaper: skipped when checkpointed, and never appended twice for the same (run, sample)
    even if the process died between the append and the checkpoint (the blob is checked first);
  - grc_issue: Idempotency-Key derived from (run_id, sample_id, step), the same on every attempt,
    every step retry and every process restart, and logged as an intent before the call.
"""

from __future__ import annotations

import json
from typing import Callable

from .grc_client import GrcClient, GrcUnavailable
from .store import Checkpoints


def idempotency_key(run_id: str, sample_id: str, step: str) -> str:
    return f"{run_id}/{sample_id}/{step}"


def _has_row(blob, run_id: str, sid: str) -> bool:
    data = blob.download_blob().readall().decode()
    for line in data.splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("run_id") == run_id and r.get("sample_id") == sid:
                return True
    return False


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
                if store.get(run_id, sid, "workpaper") is None:
                    if not _has_row(blob, run_id, sid):
                        row = {"run_id": run_id, "sample_id": sid, "control": "CM-03",
                               "conclusion": s["conclusion"], "attributes": s["attributes"]}
                        blob.append_block(json.dumps(row, sort_keys=True) + "\n")
                    store.put(run_id, sid, "workpaper", "appended")
                issue_id = store.get(run_id, sid, "grc_issue") or ""
                if s["conclusion"] == "exception" and not issue_id:
                    key = idempotency_key(run_id, sid, "grc_issue")
                    store.put(run_id, sid, "grc_issue_intent", key)
                    log(f"run {run_id}: {sid} intent grc_issue key={key}")
                    payload = {"run_id": run_id, "sample_id": sid, "control": "CM-03",
                               "title": f"CM-03 exception {sid}", "attributes": s["attributes"]}
                    issue_id = client.create_issue(payload, idempotency_key=key)
                    store.put(run_id, sid, "grc_issue", issue_id)
                if issue_id:
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
