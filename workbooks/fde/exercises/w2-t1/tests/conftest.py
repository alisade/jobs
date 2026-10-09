"""Fixtures for the visible tests; the helpers live in w2t1_support.py."""

from __future__ import annotations

import pytest
from w2t1_support import Clock, FakeIdP, settings_from_file


@pytest.fixture
def idp() -> FakeIdP:
    provider = FakeIdP(settings_from_file())
    provider.add("k-2026-09")
    return provider


@pytest.fixture
def clock() -> Clock:
    return Clock()
