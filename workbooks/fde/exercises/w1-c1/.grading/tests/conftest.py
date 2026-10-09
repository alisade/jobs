"""Fixtures for the visible tests; the helpers live in w1c1_hidden_support.py."""

from __future__ import annotations

import pytest
from w1c1_hidden_support import make_rig as _make_rig


@pytest.fixture
def make_rig():
    return _make_rig
