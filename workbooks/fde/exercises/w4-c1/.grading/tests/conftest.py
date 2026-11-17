"""Fixtures for the visible tests; helpers live in w4c1_hidden_support.py."""

from __future__ import annotations

import pytest
from w4c1_hidden_support import client


@pytest.fixture
def advisor():
    return client
