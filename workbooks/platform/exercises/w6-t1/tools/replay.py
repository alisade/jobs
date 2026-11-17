#!/usr/bin/env python3
"""Replay the commands of evidence/agent-transcript.jsonl through this checkout's guard and print the
decision for each, next to what happened on the night.

Usage: python tools/replay.py [--transcript evidence/agent-transcript.jsonl]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent.guard import check_command  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", default=str(ROOT / "evidence" / "agent-transcript.jsonl"))
    a = ap.parse_args()
    for line in Path(a.transcript).read_text().splitlines():
        ev = json.loads(line)
        if ev.get("type") != "tool_call" or ev.get("tool") != "Bash":
            continue
        d = check_command(ev["command"])
        print(f"{'ALLOW' if d.allow else 'DENY '}  (night: {ev['guard']:7})  {ev['command']}")
        print(f"        {d.reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
