"""Fixtures shared by visible and hidden tests."""
import pytest

from testkit import World


@pytest.fixture()
def world():
    return World()
