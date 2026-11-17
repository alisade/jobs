"""Loaders for the system exports in exports/. Complete; do not edit."""

from __future__ import annotations

import csv
import json
from pathlib import Path

EXP = Path(__file__).resolve().parents[1] / "exports"


def prs(d: Path = EXP) -> list[dict]:
    return json.loads((d / "prs.json").read_text())


def deploys(d: Path = EXP) -> list[dict]:
    with open(d / "deploys.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["pr_number"] = int(r["pr_number"])
    return rows


def tickets(d: Path = EXP) -> list[dict]:
    with open(d / "tickets.csv", newline="") as f:
        return list(csv.DictReader(f))


def control_total(d: Path = EXP) -> dict:
    return json.loads((d / "control_total.json").read_text())


def sampling_table(d: Path = EXP) -> dict:
    return json.loads((d / "sampling_table.json").read_text())
