"""Write the incident bundle to incident/: usage logs from before and after release 2026.10.06, the
release notes and the cost dashboard. `make setup` runs this; `make replay` re-runs the after
batch against your current code.

The after batch runs the way production does: two Function instances (two Python processes with
different PYTHONHASHSEED values, as every new process gets) sharing one model endpoint, whose
implicit cache is simulated by promptkit/fake_gemini.py with a shared prefix store.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "CM03-2026Q3-R2"
STARTED = "2026-10-07T02:00:00Z"

RELEASE_NOTES = """# ControlPilot release notes

## 2026.10.06 (deployed 2026-10-06 17:10 UTC)
- PR #2411 prompt builder cleanup: run header (run id, start time, sample id) added to the system
  instruction so every request is self-describing in the request logs; tool list now assembled
  from TOOL_REGISTRY / ENABLED_TOOLS instead of a hand-maintained list. No behaviour change intended.
- PR #2415 model bump: gemini-3.8-flash-001 -> gemini-3.8-flash-002 (vendor minor release,
  same price per the cost model).
- PR #2417 Function app: scale-out limit 1 -> 2 instances for the nightly batch.

## 2026.09.22
- Evidence policy wording (A2 aliases).
"""


def _before_rows(samples: list[dict]) -> list[dict]:
    rows = []
    for i, s in enumerate(samples):
        prompt = 5348 + (len(json.dumps(s)) // 4) - 40
        cached = 0 if i in (0, 13) else prompt - 38 - (i % 5)
        inst = "fn-0" if i < 13 else "fn-1"
        unc = prompt - cached
        cost = (unc * 0.50 + cached * 0.05 + 110 * 3.00) / 1_000_000
        rows.append({"run_id": "CM03-2026Q3-R1", "instance": inst, "sample_id": s["change_id"], "model_version": "gemini-3.8-flash-001",
                     "prompt_tokens": prompt, "cached_tokens": cached, "output_tokens": 110,
                     "latency_ms": int(180 + 0.12 * unc), "cost_usd": round(cost, 7)})
    return rows


def run_instance(label: str, store: str, out: str, ids: list[str]) -> None:
    sys.path.insert(0, str(ROOT))
    from promptkit.fake_gemini import CachingFakeClient
    from promptkit.runner import run_batch
    samples = json.loads((ROOT / "fixtures" / "samples.json").read_text())
    rows = run_batch(CachingFakeClient(store=store), [samples[i] for i in ids], run_id=RUN_ID, started_at=STARTED, instance=label)
    Path(out).write_text("".join(json.dumps(r) + "\n" for r in rows))


def after_rows(seeds=("11", "29")) -> list[dict]:
    samples = json.loads((ROOT / "fixtures" / "samples.json").read_text())
    ids = list(samples)
    halves = [ids[:13], ids[13:]]
    rows: list[dict] = []
    with tempfile.TemporaryDirectory() as tmp:
        store = str(Path(tmp) / "cache.json")
        for n, (seed, part) in enumerate(zip(seeds, halves)):
            out = str(Path(tmp) / f"rows{n}.jsonl")
            env = dict(os.environ, PYTHONHASHSEED=seed)
            subprocess.run([sys.executable, "-m", "promptkit.scenario", "instance", f"fn-{n}", store, out, *part],
                           cwd=ROOT, env=env, check=True, timeout=60)
            rows += [json.loads(x) for x in Path(out).read_text().splitlines() if x.strip()]
    return rows


def main(out_dir: str = "incident") -> int:
    sys.path.insert(0, str(ROOT))
    from promptkit.runner import summarize
    out = ROOT / out_dir
    out.mkdir(exist_ok=True)
    samples = list(json.loads((ROOT / "fixtures" / "samples.json").read_text()).values())
    before, after = _before_rows(samples), after_rows()
    (out / "usage-before.jsonl").write_text("".join(json.dumps(r) + "\n" for r in before))
    (out / "usage-after.jsonl").write_text("".join(json.dumps(r) + "\n" for r in after))
    (out / "release-notes.md").write_text(RELEASE_NOTES)
    b, a = summarize(before), summarize(after)
    dash = ["ControlPilot cost dashboard - CM-03 nightly batch (25 samples)", "",
            f"{'metric':<28}{'2026-09-29 (R1)':>18}{'2026-10-07 (R2)':>18}"]
    for k in ("calls", "prompt_tokens", "cached_tokens", "cache_hit_ratio", "cost_usd", "cost_per_100_samples_usd", "p50_latency_ms"):
        dash.append(f"{k:<28}{b[k]!s:>18}{a[k]!s:>18}")
    (out / "cost-dashboard.txt").write_text("\n".join(dash) + "\n")
    print("\n".join(dash))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "instance":
        run_instance(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
        sys.exit(0)
    sys.exit(main(*sys.argv[1:]))
