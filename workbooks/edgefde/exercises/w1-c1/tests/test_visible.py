"""Visible tests: the happy path. Hidden tests cover crashes, redelivery, schema and DQ edge cases."""

from __future__ import annotations

import json
import random
from datetime import date, datetime, timezone

import pytest

import gen
from conftest import TOPIC
from ingest.broker import FakeBroker
from ingest.models import InvalidRecord, parse_record


def test_parse_valid_v1():
    r = gen.record("pump-01", datetime(2026, 10, 14, 1, tzinfo=timezone.utc), 5, random.Random(1))
    rec = parse_record(json.dumps(r).encode())
    assert rec.key == ("pump-01", "2026-10-14T01:00:00Z")
    assert rec.schema_version == 1 and rec.temperature_c is None


def test_parse_rejects_negative_rms():
    with pytest.raises(InvalidRecord):
        parse_record(gen.INVALID_LINES[1])


def test_consumer_writes_everything(store):
    b = FakeBroker()
    b.create_topic(TOPIC, 3)
    rng = random.Random(2)
    for i in range(30):
        for dev in gen.DEVICES:
            r = gen.record(dev, datetime(2026, 10, 16, 0, i, tzinfo=timezone.utc), i, rng)
            b.produce(TOPIC, dev.encode(), json.dumps(r).encode())
    from ingest.consumer import run_until_idle

    res = run_until_idle(b.consumer("features-sink", TOPIC), store, max_records=50)
    assert res.polled == 120
    assert store.count() == 120
    assert b.lag("features-sink", TOPIC) == 0


def test_backfill_good_day_twice_is_idempotent(store, archive):
    from ingest.backfill import backfill

    day = date(2026, 10, 14)
    first = backfill(store, archive, day, gen.DEVICES)
    second = backfill(store, archive, day, gen.DEVICES)
    assert first.rows_for_day == 4 * 1440
    assert second.rows_for_day == 4 * 1440
    assert store.count() == 4 * 1440
