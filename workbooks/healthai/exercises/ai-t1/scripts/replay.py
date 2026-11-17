"""Replay a recorded transcript against fresh case state. python scripts/replay.py fixtures/transcript_incident.json PA-2026-0412"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.loop import ScriptedModel, run_agent  # noqa: E402
from agent.store import CaseStore  # noqa: E402
from agent.tools import Tools  # noqa: E402

store = CaseStore.load(ROOT / "fixtures")
msgs = run_agent(ScriptedModel.from_file(sys.argv[1]), Tools(store), sys.argv[2])
for m in msgs:
    if m["role"] == "tool":
        print(f"tool {m['name']}: {json.dumps(m['content'])[:160]}")
    elif m["role"] == "assistant":
        print(f"model: {json.dumps(m.get('tool_calls') or m.get('content'))[:160]}")
c = store.cases[sys.argv[2]]
print("final:", c.final)
print("audit:", json.dumps(c.audit))
