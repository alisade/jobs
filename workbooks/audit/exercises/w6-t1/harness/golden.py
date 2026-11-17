"""Golden-set loader. Schema v2 (2026-10-30): every row carries control_id."""

from __future__ import annotations

import json
from pathlib import Path

REQUIRED = ("sample_id", "change_id", "control_id", "labels", "overall", "labeled_by", "labeled_at")


class ProvenanceError(ValueError):
    """A golden row whose provenance makes it unusable as ground truth."""


def load_golden(path: str | Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for n, line in enumerate(Path(path).read_text().splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        missing = [k for k in REQUIRED if k not in row]
        if missing:
            raise ValueError(f"{path}:{n}: missing {missing} (schema v2)")
        rows[row["sample_id"]] = row
    return rows


def load_runs(path: str | Path) -> list[dict]:
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
