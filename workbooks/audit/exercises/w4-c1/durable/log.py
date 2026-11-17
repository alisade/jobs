"""Append-only, hash-chained execution log (JSONL). TODO: README task 3.

Each line: {"seq": n, "kind": ..., "data": {...}, "prev": <hash of line n-1 or GENESIS>, "hash": h}
where h = sha256 hex of the canonical JSON (sort_keys, separators=(",", ":")) of
{"seq", "kind", "data", "prev"}. Reopening an existing log continues the chain from its last line.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

GENESIS = "0" * 64


class ExecutionLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        # TODO: continue an existing chain (seq and prev from the last line)

    def append(self, kind: str, **data: Any) -> dict:
        """Write one line and return the record (with seq, prev and hash)."""
        raise NotImplementedError("TODO: README task 3")


def verify_log(path: str | Path) -> list[str]:
    """Return a list of problems (edited, deleted, inserted or reordered lines); empty means intact."""
    raise NotImplementedError("TODO: README task 3")
