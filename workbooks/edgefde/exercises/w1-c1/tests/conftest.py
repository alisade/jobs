from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

TOPIC = "vibration.features"


@pytest.fixture
def archive(tmp_path):
    import gen

    root = tmp_path / "archive"
    gen.write_archive(root)
    return root


@pytest.fixture
def store(tmp_path):
    from ingest.store import FeatureStore

    s = FeatureStore(tmp_path / "features.db")
    yield s
    s.close()
