import pytest

from assistant.backend import FakeAgent, Inventory
from assistant.cache import AnswerCache
from assistant.pipeline import Assistant


class Clock:
    def __init__(self, t: float = 1_764_000_000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


@pytest.fixture
def world():
    clock = Clock()
    inv = Inventory()
    agent = FakeAgent(inv)
    cache = AnswerCache(clock=clock)
    return Assistant(agent, cache), agent, inv, clock, cache
