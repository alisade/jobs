"""Fixtures for the visible tests; the helpers live in x1_hidden_support.py."""

from __future__ import annotations

import httpx
import pytest
import respx
from x1_hidden_support import FakeClock


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
async def http():
    async with httpx.AsyncClient() as client:
        yield client


@pytest.fixture
def router():
    with respx.mock(assert_all_called=False, assert_all_mocked=True) as mock:
        yield mock
