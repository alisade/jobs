from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def samples():
    return list(json.loads((ROOT / "fixtures" / "samples.json").read_text()).values())


@pytest.fixture
def root():
    return ROOT
