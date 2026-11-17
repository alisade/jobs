"""Fixtures for the visible tests; helpers live in w3t1_hidden_support.py."""

from __future__ import annotations

import pytest
from w3t1_hidden_support import Stack


@pytest.fixture
def make_stack():
    return Stack
