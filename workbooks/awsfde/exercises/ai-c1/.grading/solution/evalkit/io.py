"""Loading fixtures (done)."""

from __future__ import annotations

import json
import pathlib


def load_golden(path: pathlib.Path) -> list[dict]:
    return json.loads(path.read_text())


def load_runs(path: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
