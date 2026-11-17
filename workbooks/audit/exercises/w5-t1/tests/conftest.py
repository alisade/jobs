from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reviewagent.store import GrcStore  # noqa: E402


@pytest.fixture
def store(tmp_path):
    p = tmp_path / "grc.json"
    shutil.copy(ROOT / "fixtures" / "initial-state.json", p)
    return GrcStore(p)


@pytest.fixture
def evidence_dir():
    return ROOT / "evidence"


def recorded(change_id: str) -> list:
    return json.loads((ROOT / "fixtures" / "recorded" / f"{change_id}.json").read_text())
