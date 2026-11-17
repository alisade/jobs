"""Replay the overnight evidence-review run (recorded model responses) against state/grc.json.

make run   -> resets state/ from fixtures/initial-state.json, reviews the overnight queue, writes
              incident/trace-overnight.jsonl and prints the GRC register afterwards."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from reviewagent.agent import review
from reviewagent.scripted import scripted
from reviewagent.store import GrcStore

ROOT = Path(__file__).resolve().parent


def main() -> int:
    (ROOT / "state").mkdir(exist_ok=True)
    (ROOT / "incident").mkdir(exist_ok=True)
    shutil.copy(ROOT / "fixtures" / "initial-state.json", ROOT / "state" / "grc.json")
    store = GrcStore(ROOT / "state" / "grc.json")
    trace_path = ROOT / "incident" / "trace-overnight.jsonl"
    lines = []
    for change_id in json.loads((ROOT / "fixtures" / "overnight-queue.json").read_text()):
        script = json.loads((ROOT / "fixtures" / "recorded" / f"{change_id}.json").read_text())
        res = review(scripted(script), change_id, store, ROOT / "evidence")
        for t in res.trace:
            lines.append(json.dumps({"change_id": change_id, **t}, sort_keys=True))
        lines.append(json.dumps({"change_id": change_id, "final": res.final_text, "flags": res.flags}, sort_keys=True))
        print(f"{change_id}: tools={[t['tool'] + ('' if t['executed'] else ' (not executed)') for t in res.trace]} flags={len(res.flags)}")
    trace_path.write_text("\n".join(lines) + "\n")
    store = GrcStore(ROOT / "state" / "grc.json")
    print("\nGRC register after the run:")
    for k, v in store.data["exceptions"].items():
        last = v["history"][-1] if v["history"] else {}
        print(f"  {k} {v['change_id']} {v['status']:6} {last.get('by', '')} {last.get('comment', '')}")
    print("workpaper:", store.data["workpaper"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
