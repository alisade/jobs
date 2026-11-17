"""Fixtures for the visible tests; the helpers live in w2c1_support.py."""

from __future__ import annotations

import pytest
from w2c1_support import IdP, rsa_key


@pytest.fixture
def idp() -> IdP:
    provider = IdP()
    provider.add(rsa_key("k-2026-09"))
    return provider
