"""Runs synthetic PA cases through the (stubbed) assistant and emits logs and spans."""

from __future__ import annotations

import io
import random
import sys
from pathlib import Path

from .logsetup import build_logger
from .redact import ROSTER
from .tracing import TRACER, export_json


def run(n: int = 300, seed: int = 7, out_dir: str | Path = "out") -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stream = io.StringIO()
    log = build_logger(stream)
    TRACER.reset()
    rng = random.Random(seed)
    for i in range(1, n + 1):
        case_id = f"PA-2026-{60000 + i}"
        name = rng.choice(ROSTER)
        member = f"M-{100000 + rng.randrange(900000)}"
        with TRACER.span("pa.assess", **{"khp.case_id": case_id, "khp.member": member, "gen_ai.request.model": "stub-1"}):
            log.info(f"assessing case {case_id} for {name} ({member})", extra={"case_id": case_id})
            if rng.random() < 0.03:
                # retry path, added in 2026.10 for the eligibility timeout fix
                log.warning("eligibility retry for %s member %s", name, member, extra={"case_id": case_id})
            log.info("criteria checked", extra={"case_id": case_id})
    (out / "app.log.jsonl").write_text(stream.getvalue())
    export_json(out / "spans.json")


if __name__ == "__main__":
    run(out_dir=sys.argv[1] if len(sys.argv) > 1 else "out")
