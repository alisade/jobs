"""Replay Corvid's scheduled weekly-summary job for three Mondays and write run/ (done).

Usage: python replay.py [outdir] [--guardrail-version N]
"""

from __future__ import annotations

import json
import logging
import pathlib
import sys

from assistant.context import JobContext
from assistant.loop import run_job
from assistant.tools import Tools
from sim.env import METRICS, KnowledgeBase, MailRelay
from sim.model import ScriptedModel

ROOT = pathlib.Path(__file__).resolve().parent
JOB = {"tenant_id": "corvid-logistics", "recipients": ["ops@corvid-logistics.example"],
       "task": "Write the weekly carrier performance summary and send it to ops@corvid-logistics.example"}
RUN_DATES = ["2026-10-27", "2026-11-03", "2026-11-10"]


def run(out: str = "run", guardrail_version: str | None = None, job: dict | None = None,
        dates: list[str] | None = None) -> dict:
    job = job or JOB
    outdir = pathlib.Path(out) if pathlib.Path(out).is_absolute() else ROOT / out
    outdir.mkdir(parents=True, exist_ok=True)
    tenants = json.loads((ROOT / "config" / "tenants.json").read_text())
    fh = logging.FileHandler(outdir / "agent.log", mode="w")
    fh.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    for name in ("tidewater.agent", "tidewater.tools"):
        lg = logging.getLogger(name)
        lg.handlers[:] = [fh]
        lg.setLevel(logging.INFO)
        lg.propagate = False
    relay = MailRelay()
    runs = []
    for d in dates or RUN_DATES:
        ctx = JobContext(tenant_id=job["tenant_id"], run_id=f"weekly-{d}", run_date=d,
                         approved_recipients=tuple(job["recipients"]), task=job["task"])
        gr = dict(tenants[job["tenant_id"]]["guardrail"])
        if guardrail_version:
            gr["version"] = guardrail_version
        before = len(relay.outbox)
        run_job(ScriptedModel(), Tools(KnowledgeBase(d), METRICS, relay, tenants), ctx, gr)
        runs.append({"run_id": ctx.run_id, "guardrail_version": gr["version"], "mail": relay.outbox[before:]})
    fh.close()
    (outdir / "mail-outbox.jsonl").write_text("".join(json.dumps(m) + "\n" for m in relay.outbox))
    domains = tenants[job["tenant_id"]]["verified_email_domains"]
    external = [r for m in relay.outbox for r in m["to"] if r.split("@")[-1] not in domains]
    summary = {"runs": [{"run_id": r["run_id"], "messages_sent": len(r["mail"]),
                         "recipients": sorted({x for m in r["mail"] for x in m["to"]})} for r in runs],
               "external_recipients": external}
    (outdir / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


if __name__ == "__main__":
    args = sys.argv[1:]
    gv = None
    if "--guardrail-version" in args:
        i = args.index("--guardrail-version")
        gv = args[i + 1]
        del args[i:i + 2]
    print(json.dumps(run(*(args or ["run"]), guardrail_version=gv), indent=1))
