"""Consumer loop: poll, validate, write, THEN commit offsets."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .broker import Consumer
from .models import InvalidRecord, parse_record
from .store import FeatureStore

log = logging.getLogger("ingest.consumer")


@dataclass
class BatchResult:
    polled: int
    written: int
    quarantined: int


def run_once(consumer: Consumer, store: FeatureStore, max_records: int = 500) -> BatchResult:
    msgs = consumer.poll(max_records)
    if not msgs:
        return BatchResult(0, 0, 0)
    good, bad = [], []
    for m in msgs:
        try:
            good.append(parse_record(m.value))
        except InvalidRecord as exc:
            bad.append((m.value, str(exc), f"{m.topic}/{m.partition}/{m.offset}"))
    written = store.write_batch(good, bad)
    # Only after the transaction committed: at-least-once + idempotent upsert = effectively once.
    consumer.commit()
    log.info("batch polled=%d written=%d quarantined=%d", len(msgs), written, len(bad))
    return BatchResult(len(msgs), written, len(bad))


def run_until_idle(consumer: Consumer, store: FeatureStore, max_records: int = 500, max_batches: int = 10_000) -> BatchResult:
    total = BatchResult(0, 0, 0)
    for _ in range(max_batches):
        r = run_once(consumer, store, max_records)
        if r.polled == 0:
            break
        total = BatchResult(total.polled + r.polled, total.written + r.written, total.quarantined + r.quarantined)
    return total
