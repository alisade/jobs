"""Fixtures shared by visible and hidden tests."""
import pytest

from outbox.broker import Broker
from outbox.db import add_stage_changes, init_outbox


class Clock:
    def __init__(self, t: float = 10_000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t


@pytest.fixture()
def env(tmp_path):
    db = str(tmp_path / "pipeline.db")
    init_outbox(db)
    return {"db": db, "consumer_db": str(tmp_path / "timeline.db"), "broker": Broker(), "clock": Clock(),
            "add": lambda n: add_stage_changes(db, n)}
