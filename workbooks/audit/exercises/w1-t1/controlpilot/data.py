"""Loads the Q3 sample, deploy log and identity directory exports. Do not edit."""

from __future__ import annotations

import json
from pathlib import Path

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def samples() -> dict:
    return json.loads((FIX / "samples.json").read_text())


def deploys() -> dict:
    return json.loads((FIX / "deploys.json").read_text())


def directory() -> dict:
    return json.loads((FIX / "directory.json").read_text())
