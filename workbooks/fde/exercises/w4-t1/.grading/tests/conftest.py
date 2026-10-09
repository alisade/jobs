"""Fixtures for the visible tests; helpers live in w4t1_hidden_support.py."""

from __future__ import annotations

import pytest
from w4t1_hidden_support import make_app


@pytest.fixture
def app():
    return make_app()
