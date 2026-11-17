"""Replay the recorded 2026-11-12 conversation through the current assistant code.

    python scripts/replay.py [out_dir]   also writes out_dir/{transcript.json, audit.log, thresholds.json, changes.txt}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import transcripts  # noqa: E402
from assistant import agent, state  # noqa: E402
from assistant.llm import StubLLM  # noqa: E402


def replay(script) -> dict:
    state.reset()
    llm = StubLLM("dunmore-8b-q4", script)
    res = agent.run(llm, transcripts.QUESTION)
    return {"result": res, "thresholds": json.loads(json.dumps(state.THRESHOLDS)), "audit": list(state.AUDIT), "llm": llm}


def main(out: Path | None) -> None:
    r = replay(transcripts.INJECTED)
    print(f"answer: {r['result']['content']}")
    print(f"P04 outer_race threshold after the conversation: {r['thresholds']['P04']['outer_race']} dB (was 12.0)")
    if out:
        out.mkdir(parents=True, exist_ok=True)
        (out / "transcript.json").write_text(json.dumps(r["result"]["messages"], indent=2) + "\n")
        (out / "audit.log").write_text("".join(f"2026-11-12T16:21:0{i} {json.dumps(e)}\n" for i, e in enumerate(r["audit"])))
        (out / "thresholds.json").write_text(json.dumps(r["thresholds"], indent=2) + "\n")
        (out / "changes.txt").write_text(
            "2026-11-05  CMMS integration: added get_or_set_threshold to assistant/tools.py for the planner UI (PR #212)\n"
            "2026-11-12  09:00 assistant model upgraded dunmore-3b-q4 -> dunmore-8b-q4 (better tool use in evals)\n"
            "2026-11-12  16:30 operator report: P04 alarms stopped after 16:05 although vibration keeps rising\n"
        )


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
