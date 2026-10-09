"""Fixtures for the visible tests; helpers live in x2_hidden_support.py."""

from __future__ import annotations

import pytest
from x2_hidden_support import Capture, reset_trust_loggers


@pytest.fixture
def capture():
    cap = Capture()
    yield cap
    reset_trust_loggers()
