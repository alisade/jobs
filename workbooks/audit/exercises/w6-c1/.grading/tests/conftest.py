from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evalkit.data import load_json, load_labels, load_runs  # noqa: E402


@pytest.fixture
def labels():
    return load_labels(ROOT / "data" / "labels.jsonl")


@pytest.fixture
def runs():
    return load_runs(ROOT / "data" / "runs.jsonl")


@pytest.fixture
def prices():
    return load_json(ROOT / "data" / "prices.json")


@pytest.fixture
def baseline():
    return load_json(ROOT / "baseline.json")
