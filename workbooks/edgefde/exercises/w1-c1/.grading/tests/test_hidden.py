"""Hidden tests for edgefde/w1-c1: contract edge cases, crash safety, redelivery, ordering, DQ, CLI."""

from __future__ import annotations

import json
import random
import sqlite3
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import gen  # noqa: E402
from ingest.broker import FakeBroker  # noqa: E402
from ingest.models import InvalidRecord, parse_record  # noqa: E402
from ingest.store import FeatureStore  # noqa: E402

TOPIC = "vibration.features"
T0 = datetime(2026, 10, 16, 0, tzinfo=timezone.utc)


def rec(dev="pump-01", i=0, seq=None, **over):
    return gen.record(dev, T0 + timedelta(minutes=i), i if seq is None else seq, random.Random(i), **over)


def enc(r):
    return json.dumps(r).encode()


def broker_with(n=40, devices=gen.DEVICES, extra=()):
    b = FakeBroker()
    b.create_topic(TOPIC, 3)
    for i in range(n):
        for dev in devices:
            b.produce(TOPIC, dev.encode(), enc(rec(dev, i)))
    for key, value in extra:
        b.produce(TOPIC, key, value)
    return b


@pytest.fixture
def store(tmp_path):
    s = FeatureStore(tmp_path / "f.db")
    yield s
    s.close()


# ---- contract -------------------------------------------------------------------------------

@pytest.mark.parametrize("line", gen.INVALID_LINES, ids=["naive_ts", "neg_rms", "bands3", "not_json", "bad_device"])
def test_contract_rejects(line):
    with pytest.raises(InvalidRecord) as ei:
        parse_record(line)
    assert str(ei.value).strip(), "InvalidRecord needs a reason for the quarantine table"


def test_contract_rejects_nan_and_inf():
    for bad in (float("nan"), float("inf")):
        raw = json.dumps(rec(rms=bad)).encode()  # json emits NaN / Infinity
        with pytest.raises(InvalidRecord):
            parse_record(raw)


def test_contract_v2_and_unknown_fields():
    r = rec(version=2)
    r["firmware"] = "4.2.0"  # a field from a future schema must not break the consumer
    p = parse_record(enc(r))
    assert p.schema_version == 2 and p.temperature_c is not None


def test_key_normalises_offset_to_utc():
    r = rec()
    r["window_start"] = "2026-10-15T20:00:00-04:00"
    assert parse_record(enc(r)).key == ("pump-01", "2026-10-16T00:00:00Z")


# ---- consumer ---------------------------------------------------------------------------------

def test_invalid_messages_quarantined_and_do_not_block(store):
    from ingest.consumer import run_until_idle

    b = broker_with(10, extra=[(b"pump-02", line) for line in gen.INVALID_LINES])
    res = run_until_idle(b.consumer("g", TOPIC), store, max_records=7)
    assert store.count() == 40
    assert store.quarantine_count() == 5
    assert res.quarantined == 5
    assert b.lag("g", TOPIC) == 0
    src = store.conn.execute("SELECT source FROM quarantine").fetchall()
    assert all(s[0].startswith(TOPIC + "/") for s in src), "quarantine source must be <topic>/<partition>/<offset>"


def test_crash_after_poll_redelivers_without_duplicates(store):
    from ingest.consumer import run_once, run_until_idle

    b = broker_with(25)
    c = b.consumer("g", TOPIC)
    run_once(c, store, max_records=30)
    c.poll(30)  # polled, then the process dies before writing: nothing committed for these
    del c
    run_until_idle(b.consumer("g", TOPIC), store, max_records=30)
    assert store.count() == 100
    assert b.lag("g", TOPIC) == 0


class ExplodingStore:
    def __init__(self, inner, fail_on_call):
        self.inner, self.fail_on_call, self.calls = inner, fail_on_call, 0

    def write_batch(self, records, quarantined=()):
        self.calls += 1
        if self.calls == self.fail_on_call:
            raise sqlite3.OperationalError("disk I/O error")
        return self.inner.write_batch(records, quarantined)

    def __getattr__(self, name):
        return getattr(self.inner, name)


def test_failed_write_does_not_commit_offsets(store):
    from ingest.consumer import run_once, run_until_idle

    b = broker_with(20)
    c = b.consumer("g", TOPIC)
    run_once(c, store, max_records=20)
    committed_before = b.committed("g", TOPIC)
    with pytest.raises(sqlite3.OperationalError):
        run_once(c, ExplodingStore(store, 1), max_records=20)
    assert b.committed("g", TOPIC) == committed_before, "offsets must not move when the write failed"
    run_until_idle(b.consumer("g", TOPIC), store, max_records=20)
    assert store.count() == 80


def test_batch_is_atomic(tmp_path):
    """A failure in the middle of a batch must leave neither features nor quarantine rows behind."""
    s = FeatureStore(tmp_path / "a.db")
    good = [parse_record(enc(rec(i=i))) for i in range(5)]

    class Boom(Exception):
        pass

    def bad_iter():
        yield from good[:3]
        raise Boom()

    with pytest.raises(Boom):
        s.write_batch(bad_iter(), [(b"x", "reason", "t/0/1")])
    assert s.count() == 0
    assert s.quarantine_count() == 0
    s.close()


def test_redelivered_quarantine_not_duplicated(store):
    from ingest.consumer import run_once, run_until_idle

    b = broker_with(2, extra=[(b"pump-02", gen.INVALID_LINES[3])])
    c = b.consumer("g", TOPIC)
    msgs = c.poll(100)  # read everything, crash before commit
    assert msgs
    run_until_idle(b.consumer("g", TOPIC), store)
    # simulate a second redelivery of the same offsets (e.g. a rebalance before commit)
    b._committed.clear()
    run_until_idle(b.consumer("g", TOPIC), store)
    assert store.count() == 8
    assert store.quarantine_count() == 1


def test_higher_seq_wins_and_old_replay_does_not_overwrite(store):
    newer = rec(i=3, seq=50, rms=1.25)
    older = rec(i=3, seq=10, rms=9.75)
    store.write_batch([parse_record(enc(newer))])
    store.write_batch([parse_record(enc(older))])
    got = store.get("pump-01", "2026-10-16T00:03:00Z")
    assert got["seq"] == 50 and got["rms"] == pytest.approx(1.25)
    store.write_batch([parse_record(enc(rec(i=3, seq=60, rms=2.5)))])
    assert store.get("pump-01", "2026-10-16T00:03:00Z")["seq"] == 60


# ---- data quality and backfill -----------------------------------------------------------------

@pytest.fixture
def archive(tmp_path):
    root = tmp_path / "archive"
    gen.write_archive(root)
    return root


def test_good_day_backfill_counts(store, archive):
    from ingest.backfill import backfill

    res = backfill(store, archive, date(2026, 10, 14), gen.DEVICES)
    assert res.valid == 4 * 1440 + len(range(0, 4 * 1440, 97))
    assert res.quarantined == 5
    assert res.rows_for_day == 4 * 1440
    assert store.quarantine_count() == 5
    backfill(store, archive, date(2026, 10, 14), gen.DEVICES)
    assert store.quarantine_count() == 5, "re-running a backfill must not duplicate quarantine rows"


def test_gappy_day_fails_and_writes_nothing(store, archive):
    from ingest.backfill import backfill
    from ingest.dq import DataQualityError

    with pytest.raises(DataQualityError) as ei:
        backfill(store, archive, date(2026, 10, 15), gen.DEVICES)
    assert any(i.check == "completeness" and "pump-03" in i.detail for i in ei.value.issues)
    assert store.count() == 0


def test_dq_checks_each_rule():
    from ingest.dq import check_day

    day = date(2026, 10, 14)
    recs = [parse_record(enc(r)) for r in gen.day_records(day)]
    assert check_day(recs, day, gen.DEVICES) == []
    missing = check_day([r for r in recs if r.device_id != "pump-02"], day, gen.DEVICES)
    assert [i.check for i in missing] == ["device_present"]
    stray = recs + [parse_record(enc(gen.record("pump-01", datetime(2026, 10, 15, 0, 5, tzinfo=timezone.utc), 1, random.Random(0))))]
    assert "in_partition" in [i.check for i in check_day(stray, day, gen.DEVICES)]
    hot = [parse_record(enc({**r.model_dump(mode="json"), "rms": 80.0})) if n % 50 == 0 else r for n, r in enumerate(recs)]
    assert "rms_range" in [i.check for i in check_day(hot, day, gen.DEVICES)]
    dup_only = recs + recs[:100]
    assert check_day(dup_only, day, gen.DEVICES) == [], "duplicates must not inflate or break completeness"


def test_backfill_after_live_ingest_no_duplicates(store, archive):
    from ingest.backfill import backfill
    from ingest.consumer import run_until_idle

    b = FakeBroker()
    b.create_topic(TOPIC, 3)
    for r in gen.day_records(date(2026, 10, 14))[:500]:
        b.produce(TOPIC, r["device_id"].encode(), enc(r))
    run_until_idle(b.consumer("g", TOPIC), store)
    assert store.count() == 500
    backfill(store, archive, date(2026, 10, 14), gen.DEVICES)
    assert store.count() == 4 * 1440


def test_cli_exit_codes(tmp_path, archive):
    db = tmp_path / "cli.db"
    args = [sys.executable, "-m", "ingest.backfill", "--db", str(db), "--archive", str(archive),
            "--devices", ",".join(gen.DEVICES)]
    ok = subprocess.run(args + ["--day", "2026-10-14"], cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert ok.returncode == 0, ok.stderr
    bad = subprocess.run(args + ["--day", "2026-10-15"], cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert bad.returncode == 2
    assert "pump-03" in (bad.stderr + bad.stdout)
