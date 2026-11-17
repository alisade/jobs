"""Append-only audit log. Provided; do not change.

Each entry: ts, agent_id, on_behalf_of, tenant, tool, args_sha256, outcome, trace_id.
Store the hash of the arguments, not the arguments: activity subjects can contain personal data.
"""

from __future__ import annotations

import copy
import hashlib
import json

FIELDS = ("ts", "agent_id", "on_behalf_of", "tenant", "tool", "args_sha256", "outcome", "trace_id")
OUTCOMES = ("ok", "denied", "not_found", "invalid", "error")


def args_digest(args: dict) -> str:
    return hashlib.sha256(json.dumps(args, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class AuditLog:
    def __init__(self) -> None:
        self._entries: list[dict] = []

    def append(self, entry: dict) -> None:
        missing = [f for f in FIELDS if f not in entry]
        if missing:
            raise ValueError(f"audit entry missing {missing}")
        if entry["outcome"] not in OUTCOMES:
            raise ValueError(f"bad outcome {entry['outcome']}")
        self._entries.append(copy.deepcopy({f: entry[f] for f in FIELDS}))

    def entries(self) -> list[dict]:
        return copy.deepcopy(self._entries)
