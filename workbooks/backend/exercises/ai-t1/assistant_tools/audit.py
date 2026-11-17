"""Append-only audit log of tool calls (a table in production; a list here)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

AUDIT: list[dict] = []


def args_sha256(args: dict) -> str:
    return hashlib.sha256(json.dumps(args, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def record(entry: dict) -> None:
    entry = dict(entry)
    entry.setdefault("ts", datetime.now(timezone.utc).isoformat())
    AUDIT.append(entry)
