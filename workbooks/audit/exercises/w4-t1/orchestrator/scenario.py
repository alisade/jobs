"""Replay the 2026-10-01 02:00 UTC publish run of CM03-2026Q3 against the local fakes and write the
incident bundle to incident/. `make setup` runs this; run it again after a fix to compare."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .fakes import Clock, FakeAppendBlob, FakeGrcServer
from .run import run_publish
from .store import Checkpoints

RUN_ID = "CM03-2026Q3"
# Request-level faults seen in the GRC gateway that night (from the gateway's own records).
FAULTS = {1: "commit_timeout", 2: "commit_timeout", 4: "429", 6: "commit_timeout"}


def samples() -> list[dict]:
    ok = {"approval_before_deploy": "pass", "independent_approver": "pass", "linked_change": "pass", "tests_passed": "pass"}
    rows = []
    for sid, bad in [("CHG-104118", None), ("CHG-104390", "independent_approver"), ("CHG-104455", None),
                     ("CHG-104502", "approval_before_deploy"), ("CHG-104577", None), ("CHG-104611", "tests_passed")]:
        attrs = dict(ok)
        if bad:
            attrs[bad] = "exception"
        rows.append({"sample_id": sid, "conclusion": "exception" if bad else "pass", "attributes": attrs})
    return rows


def main(out_dir: str = "incident") -> int:
    out = Path(out_dir)
    out.mkdir(exist_ok=True)
    for p in out.iterdir():
        p.unlink()
    clock = Clock()
    server = FakeGrcServer(faults=dict(FAULTS), clock=clock)
    blob = FakeAppendBlob(f"workpapers/{RUN_ID}/workpaper.jsonl")
    store = Checkpoints(out / "checkpoint.db")
    lines: list[str] = []
    log = lambda m: lines.append(f"{clock.iso()} controlpilot-publish {m}")  # noqa: E731
    log(f"run {RUN_ID}: publish stage starting, {len(samples())} samples")
    res = run_publish(RUN_ID, samples(), server=server, blob=blob, store=store, sleep=clock.sleep, log=log)
    log(f"run {RUN_ID}: publish stage finished: {len(res['published'])} published, {len(res['failed'])} failed")
    (out / "orchestrator.log").write_text("\n".join(lines) + "\n")
    (out / "grc-gateway.log").write_text("\n".join(server.log) + "\n")
    (out / "grc-issues.json").write_text(json.dumps(
        [{k: i[k] for k in ("issue_id", "sample_id", "run_id", "request_id", "idempotency_key")} for i in server.issues], indent=2) + "\n")
    (out / "workpaper.jsonl").write_text(blob.download_blob().readall().decode())
    (out / "checkpoint-dump.txt").write_text("run_id|sample_id|step|value\n" + "\n".join("|".join(r) for r in store.dump()) + "\n")
    print(f"incident bundle in {out}/: {len(server.issues)} GRC issues for "
          f"{sum(1 for s in samples() if s['conclusion'] == 'exception')} exceptions, {len(blob.rows())} workpaper rows for {len(samples())} samples")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
