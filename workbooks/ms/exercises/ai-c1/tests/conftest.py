import json
from pathlib import Path

import pytest

from parts_agent.backend import Backend
from parts_agent.fake_model import FakeModelClient
from parts_agent.loop import run_turn
from parts_agent.session import Session

FIX = Path(__file__).resolve().parent.parent / "fixtures"


def replay(name: str, max_turns: int = 8):
    fx = json.loads((FIX / name).read_text())
    client = FakeModelClient(fx["turns"])
    session = Session(backend=Backend())
    results = []
    for i, text in enumerate(fx["user_turns"]):
        for qid in fx.get("confirm_before_turn", {}).get(str(i), []):
            session.confirm(qid)
        results.append(run_turn(client, session, text, max_turns=max_turns))
    return client, session, results


@pytest.fixture
def replay_fixture():
    return replay
