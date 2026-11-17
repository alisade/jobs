import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def call(cid, name, **args):
    return {"id": cid, "name": name, "arguments": args}


def tool_turn(*calls):
    return {"role": "assistant", "tool_calls": list(calls)}


def final(answer="P04 alerted on an outer-race score of 18.4 dB.", citations=("c1",), confidence=0.8, action="inspect_next_window", raw=None):
    if raw is not None:
        return {"role": "assistant", "content": raw}
    return {"role": "assistant", "content": json.dumps({"answer": answer, "citations": list(citations),
                                                         "confidence": confidence, "recommended_action": action})}
