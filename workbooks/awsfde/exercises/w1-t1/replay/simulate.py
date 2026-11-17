"""Replay the Monday peak and write logs and a CloudWatch-style dashboard.

    python -m replay.simulate --out run                 # both Mondays: previous and current release
    python -m replay.simulate --out run --only current  # this checkout on 2026-11-09 (after a fix)
"""

from __future__ import annotations

import argparse
import json
import pathlib

from .sim import load_release, run
from .traffic import clock

HERE = pathlib.Path(__file__).resolve().parent.parent


def dashboard(title: str, res: dict) -> str:
    s = res["summary"]
    lines = [f"== {title}  (release {s['release']}, {s['day']} 08:50-09:20)",
             "minute    req  200  400  429  500  503  504  bedrock_inv  throttles  p95_ms  max_conc"]
    for k, v in res["minutes"].items():
        lines.append(f"{clock(k * 60)[:5]}   {v['requests']:4d} {v['s200']:4d} {v['s400']:4d} {v['s429']:4d} "
                     f"{v['s500']:4d} {v['s503']:4d} {v['s504']:4d}  {v['bedrock_invocations']:11d}  "
                     f"{v['throttles']:9d}  {v['p95_ms']:6d}  {v['max_concurrency']:8d}")
    lines.append("summary: " + json.dumps({k: s[k] for k in (
        "requests", "statuses", "error_rate", "p50_ms", "p95_ms", "model_calls", "throttles",
        "max_concurrency")}))
    return "\n".join(lines)


def write(out: pathlib.Path, label: str, res: dict) -> None:
    d = out / "logs" / res["summary"]["day"]
    d.mkdir(parents=True, exist_ok=True)
    with (d / "requests.log").open("w") as f:
        for r in res["requests"]:
            f.write(json.dumps(r) + "\n")
    (d / "summary.json").write_text(json.dumps(res["summary"], indent=2) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="run")
    ap.add_argument("--only", choices=["current"], default=None)
    a = ap.parse_args()
    out = HERE / a.out
    out.mkdir(parents=True, exist_ok=True)
    panels = []
    if a.only is None:
        prev = load_release(HERE / "evidence" / "previous_release", "prev_answer_svc")
        r1 = run(prev, "2026-11-02")
        write(out, "previous", r1)
        panels.append(dashboard("Monday 2026-11-02", r1))
    cur = load_release(HERE, "current_answer_svc")
    r2 = run(cur, "2026-11-09")
    if a.only is None:
        write(out, "current", r2)
        panels.append(dashboard("Monday 2026-11-09", r2))
        (out / "dashboard.txt").write_text("\n\n".join(panels) + "\n")
        print(f"wrote {out}/dashboard.txt and {out}/logs/")
    else:
        d = out / "replay-current"
        d.mkdir(parents=True, exist_ok=True)
        (d / "dashboard.txt").write_text(dashboard("Replay of this checkout on 2026-11-09", r2) + "\n")
        print(dashboard("Replay of this checkout on 2026-11-09", r2).splitlines()[-1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
