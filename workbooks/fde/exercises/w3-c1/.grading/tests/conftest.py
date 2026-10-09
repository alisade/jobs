"""Fixtures for the visible tests; the helpers live in w3c1_hidden_support.py."""

from __future__ import annotations

import pytest
from w3c1_hidden_support import make_stack as _make_stack


@pytest.fixture
def make_stack():
    return _make_stack
