"""Loaders for the labeled set, recorded runs and price table. Complete."""

from __future__ import annotations

import json
from pathlib import Path


def read_jsonl(path: str | Path) -> list[dict]:
    rows = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def load_labels(path: str | Path) -> dict[str, dict]:
    """sample_id -> {"labels": {attribute: outcome}, "overall": outcome, "labeled_by", "labeled_at", ...}"""
    return {r["sample_id"]: r for r in read_jsonl(path)}


def load_runs(path: str | Path) -> list[dict]:
    """One row per (sample_id, run): outputs, overall, usage {prompt_tokens, output_tokens, cached_tokens}, latency_ms."""
    return read_jsonl(path)


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())
