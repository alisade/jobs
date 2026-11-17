"""Hidden checks for edgefde/w1-t1: no loss and no duplicates at any crash point; batching kept."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import simulate  # noqa: E402
from sink.broker import FakeBroker  # noqa: E402
from sink.store import WindowStore  # noqa: E402


class KillAfterWrite:
    """The write commits, then the process dies before anything else runs."""

    def __init__(self, inner, on_calls=(3, 9, 17)):
        self.inner, self.on_calls, self.calls = inner, set(on_calls), 0

    def write_rows(self, rows):
        n = self.inner.write_rows(rows)
        self.calls += 1
        if self.calls in self.on_calls:
            raise simulate.Killed()
        return n

    def __getattr__(self, name):
        return getattr(self.inner, name)


class KillBeforeWrite(KillAfterWrite):
    def write_rows(self, rows):
        self.calls += 1
        if self.calls in self.on_calls:
            raise simulate.Killed()
        return self.inner.write_rows(rows)


def test_restarts_lose_nothing(tmp_path):
    res = simulate.run_scenario(tmp_path / "a.db")
    assert res["distinct"] == 8640
    assert res["lag"] == 0


def test_restarts_duplicate_nothing(tmp_path):
    res = simulate.run_scenario(tmp_path / "a.db")
    assert res["rows"] == res["distinct"] == 8640


def test_kill_after_write_before_commit(tmp_path):
    res = simulate.run_scenario(tmp_path / "k.db", store_wrapper=KillAfterWrite)
    assert res["distinct"] == 8640, "lost windows"
    assert res["rows"] == 8640, "redelivered rows were written twice: the write is not idempotent"


def test_kill_before_write(tmp_path):
    res = simulate.run_scenario(tmp_path / "k2.db", store_wrapper=KillBeforeWrite)
    assert res["distinct"] == 8640 and res["rows"] == 8640


def test_offsets_never_ahead_of_the_table(tmp_path, monkeypatch):
    seen = []
    holder = {}

    def wrap(store):
        holder["s"] = store
        return store

    orig = FakeBroker._commit

    def spy(self, group, topic, offsets):
        seen.append((sum(offsets.values()), holder["s"].distinct()))
        return orig(self, group, topic, offsets)

    monkeypatch.setattr(FakeBroker, "_commit", spy)
    simulate.run_scenario(tmp_path / "s.db", store_wrapper=wrap)
    assert seen, "the sink never committed offsets"
    bad = [(c, n) for c, n in seen if c > n]
    assert not bad, f"committed offsets ran ahead of durable rows {bad[:3]}"


def test_auto_commit_disabled():
    import sink.consumer as c

    b = FakeBroker()
    b.create_topic(c.TOPIC, 3)
    s = c.Sink(b, WindowStore(":memory:"))
    assert s.consumer.enable_auto_commit is False


def test_batching_kept(tmp_path):
    res = simulate.run_scenario(tmp_path / "t.db", restarts={})
    assert res["transactions"] <= 40, f"{res['transactions']} transactions: the fix must keep batched writes"


def test_store_write_is_idempotent(tmp_path):
    s = WindowStore(tmp_path / "i.db")
    rows = [("pump-01", "2026-10-20T00:00:00Z", 0.5, "DUN-P001"), ("pump-01", "2026-10-20T00:01:00Z", 0.6, "DUN-P001")]
    s.write_rows(rows)
    s.write_rows(rows)
    assert s.count() == 2
