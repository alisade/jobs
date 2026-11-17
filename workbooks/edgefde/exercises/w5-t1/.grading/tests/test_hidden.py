"""Hidden tests for edgefde/w5-t1: exactly-once to the cloud under lost acks, partial acks, restarts."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import outage  # noqa: E402
from gateway.buffer import Buffer  # noqa: E402
from gateway.cloud import IngestServer, Uplink  # noqa: E402


@pytest.mark.parametrize("seed", [1, 4, 9])
def test_outage_day_exactly_once(tmp_path, seed):
    r = outage.run_day(tmp_path / "a.db", seed=seed)
    assert r["server"] == r["truth"] and r["pending"] == 0


def test_heavy_ack_loss_exactly_once(tmp_path):
    r = outage.run_day(tmp_path / "b.db", ack_loss=0.9, partial_loss=0.3)
    assert r["server"] == r["truth"]


def test_partial_acks_do_not_lose_rows(tmp_path):
    r = outage.run_day(tmp_path / "c.db", max_per_request=7, outage=(100, 140), flaky=(0, 0))
    assert r["server"] == r["truth"] and r["pending"] == 0


def test_restart_mid_replay(tmp_path):
    r = outage.run_day(tmp_path / "d.db", restart_at=150)
    assert r["server"] == r["truth"]


def test_same_event_keeps_its_id_across_resends(tmp_path):
    server = IngestServer()
    link = Uplink(server)
    link.ack_loss = 1.0
    b = Buffer(tmp_path / "e.db")
    b.capture("pump-01", "2026-11-04T09:00:00Z", "alert", {"score": 0.9})
    b.replay(link, max_batches=3)
    assert server.received == 3 and len(server.events) == 1
    assert b.pending_count() == 1, "an unacknowledged event must stay pending"
    link.ack_loss = 0.0
    b.replay(link)
    assert len(server.events) == 1 and b.pending_count() == 0


def test_order_per_device_preserved(tmp_path):
    r = outage.run_day(tmp_path / "f.db", seed=2)
    srv = r["server_obj"]
    for dev in outage.DEVICES:
        ws = [srv.events[e]["window_start"] for e in srv.order if srv.events[e]["device_id"] == dev]
        assert ws == sorted(ws), dev


def test_buffer_cap_still_enforced(tmp_path):
    b = Buffer(tmp_path / "g.db", max_rows=100)
    for i in range(250):
        b.capture("pump-01", f"2026-11-04T{i // 60:02d}:{i % 60:02d}:00Z", "features", {"i": i})
    assert b.pending_count() == 100 and b.dropped() == 150


def test_capture_of_a_duplicate_reading_is_one_event(tmp_path):
    server = IngestServer()
    b = Buffer(tmp_path / "h.db")
    for _ in range(2):  # the sensor driver re-emits the last window after a reconnect
        b.capture("pump-02", "2026-11-04T10:00:00Z", "features", {"rms": 0.5})
    b.replay(Uplink(server))
    assert len(server.events) == 1
