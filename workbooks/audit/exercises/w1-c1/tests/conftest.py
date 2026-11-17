from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from controlpilot import systems  # noqa: E402
from controlpilot.fake_gemini import FakeClient, load_script  # noqa: E402


@pytest.fixture
def samples():
    return systems.samples()


@pytest.fixture
def tools():
    return systems.tools()


@pytest.fixture
def directory():
    return systems.directory()


@pytest.fixture
def deploys():
    return systems.deploys()


@pytest.fixture
def client_for():
    def make(sample_key: str) -> FakeClient:
        return FakeClient(load_script(ROOT / "fixtures" / "scripts" / f"{sample_key}.json"))
    return make
