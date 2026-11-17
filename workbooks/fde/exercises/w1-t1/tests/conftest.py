"""Fixtures for the visible tests; the helpers live in w1t1_support.py."""

from __future__ import annotations

import pytest
from w1t1_support import FLAGS


@pytest.fixture
def flags():
    return dict(FLAGS)
