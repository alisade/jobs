"""Pytest fixtures shared by the visible and hidden tests."""
import pytest

from fakedataverse import FakeServer


@pytest.fixture()
def server():
    with FakeServer() as s:
        yield s


@pytest.fixture()
def sleeps(monkeypatch):
    """Record sleep calls instead of sleeping. Patch target: woodgrove_sync.client.time.sleep."""
    calls = []
    import woodgrove_sync.client as client_mod
    monkeypatch.setattr(client_mod.time, "sleep", lambda s: calls.append(s))
    return calls
