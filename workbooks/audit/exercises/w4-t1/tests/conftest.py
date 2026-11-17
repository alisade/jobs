from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from orchestrator.fakes import Clock, FakeAppendBlob, FakeGrcServer  # noqa: E402
from orchestrator.scenario import RUN_ID, samples  # noqa: E402
from orchestrator.store import Checkpoints  # noqa: E402


@pytest.fixture
def world(tmp_path):
    def make(faults=None, run_id=RUN_ID, server=None, blob=None, db=None):
        clock = Clock()
        w = {
            "server": server or FakeGrcServer(faults=dict(faults or {}), clock=clock),
            "blob": blob or FakeAppendBlob("workpapers/x/workpaper.jsonl"),
            "store": Checkpoints(db or tmp_path / "cp.db"),
            "sleeps": [], "lines": [], "run_id": run_id, "samples": samples(),
        }

        def sleep(s):
            w["sleeps"].append(s)
            w["server"].clock.sleep(s)
        w["sleep"] = sleep
        w["log"] = w["lines"].append
        return w
    return make



@pytest.fixture
def h():
    """Helper functions: publish, issues_by_sample, rows_by_sample."""
    import types
    return types.SimpleNamespace(publish=publish, issues_by_sample=issues_by_sample, rows_by_sample=rows_by_sample)


def publish(w):
    from orchestrator.run import run_publish
    return run_publish(w["run_id"], w["samples"], server=w["server"], blob=w["blob"], store=w["store"],
                       sleep=w["sleep"], log=w["log"])


def issues_by_sample(server):
    out = {}
    for i in server.issues:
        out.setdefault(i["sample_id"], []).append(i["issue_id"])
    return out


def rows_by_sample(blob):
    out = {}
    for r in blob.rows():
        out[r["sample_id"]] = out.get(r["sample_id"], 0) + 1
    return out
