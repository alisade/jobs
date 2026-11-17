"""Append-only, hash-chained execution log (JSONL).

Each line: {"seq": n, "kind": ..., "data": {...}, "prev": <hash of line n-1 or GENESIS>, "hash": h}
where h = sha256 of the canonical JSON of {"seq", "kind", "data", "prev"}. Reopening the log continues
the chain from the last line, so a resumed run extends the same trail.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

GENESIS = "0" * 64


def _digest(seq: int, kind: str, data: Any, prev: str) -> str:
    body = json.dumps({"seq": seq, "kind": kind, "data": data, "prev": prev}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode()).hexdigest()


class ExecutionLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.seq, self.prev = 0, GENESIS
        if self.path.exists():
            lines = [ln for ln in self.path.read_text().splitlines() if ln.strip()]
            if lines:
                last = json.loads(lines[-1])
                self.seq, self.prev = last["seq"] + 1, last["hash"]

    def append(self, kind: str, **data: Any) -> dict:
        data = json.loads(json.dumps(data, sort_keys=True))
        rec = {"seq": self.seq, "kind": kind, "data": data, "prev": self.prev}
        rec["hash"] = _digest(self.seq, kind, data, self.prev)
        with self.path.open("a") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
            f.flush()
        self.seq, self.prev = self.seq + 1, rec["hash"]
        return rec


def verify_log(path: str | Path) -> list[str]:
    """Return a list of problems; empty means the chain is intact."""
    problems: list[str] = []
    prev, expected_seq = GENESIS, 0
    p = Path(path)
    if not p.exists():
        return [f"{p}: missing"]
    for n, line in enumerate(p.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            problems.append(f"line {n}: not JSON")
            return problems
        if rec.get("seq") != expected_seq:
            problems.append(f"line {n}: seq {rec.get('seq')} expected {expected_seq}")
        if rec.get("prev") != prev:
            problems.append(f"line {n}: prev hash does not match line before")
        if rec.get("hash") != _digest(rec.get("seq"), rec.get("kind"), rec.get("data"), rec.get("prev")):
            problems.append(f"line {n}: hash does not match content")
        prev, expected_seq = rec.get("hash"), expected_seq + 1
    return problems
