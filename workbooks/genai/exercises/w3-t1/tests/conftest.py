import pytest

from assistant_gateway.clock import FakeClock
from assistant_gateway.gateway import Gateway
from assistant_gateway.provider import FakeProvider

QUESTION = [
    {"role": "system", "content": "You are Kestrel Outfitters' shopping assistant. " * 20},
    {"role": "user", "content": "Compare the Ridgeline 2P and the Basecamp 3P for a family of three."},
]


def make(script=None):
    clock = FakeClock()
    provider = FakeProvider(clock=clock, script=list(script or []))
    return Gateway(provider=provider, clock=clock), provider, clock


@pytest.fixture
def question():
    return [dict(m) for m in QUESTION]
