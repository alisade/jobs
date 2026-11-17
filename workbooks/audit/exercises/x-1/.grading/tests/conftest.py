from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def claims():
    return json.loads((ROOT / "wifsim" / "sample_claims.json").read_text())


@pytest.fixture
def config_dir():
    return ROOT / "config"
