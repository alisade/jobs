from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from durable import agent  # noqa: E402
from durable.fakes import FakeBlobContainer, FakeGrc  # noqa: E402
from durable.run import TestRun  # noqa: E402


@pytest.fixture
def world(tmp_path):
    """Shared systems that survive a 'process restart': blob, GRC, db and log paths."""
    agent.CALLS.clear()
    w = {"blob": FakeBlobContainer(), "grc": FakeGrc(), "db": tmp_path / "run.db", "log": tmp_path / "run.log.jsonl"}

    def start(crash_at=None, run_id="CM03-2026Q3", preparer="ralvarez"):
        return TestRun(run_id, agent.sample_ids(), db_path=w["db"], log_path=w["log"], preparer=preparer,
                       evidence_fn=agent.fetch_evidence, test_fn=agent.test_sample,
                       blob=w["blob"], grc=w["grc"], crash_at=crash_at)

    w["start"] = start
    w["calls"] = agent.CALLS
    return w
