import pytest
from fastapi.testclient import TestClient

from assistant.app import create_app
from assistant.llm import ScriptedLLM
from assistant.store import Store


class Clock:
    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


@pytest.fixture
def make():
    """make(steps) -> (TestClient, llm, store, clock)"""

    def _make(steps, store=None):
        llm = ScriptedLLM(steps)
        store = store or Store()
        clock = Clock()
        app = create_app(llm, store, clock)
        return TestClient(app, raise_server_exceptions=False), llm, store, clock, app

    return _make


def ana(c, message, conversation_id=None):
    body = {"message": message}
    if conversation_id:
        body["conversation_id"] = conversation_id
    return c.post("/chat", json=body, headers={"X-User-Id": "u-ana"})
