"""vibration.features -> windows table, with asset enrichment and batched writes.

Fixed: auto-commit is off; offsets are committed only after the batch is durable in
SQLite, and the table write is idempotent so a crash between write and commit only
causes a harmless redelivery.
"""

from __future__ import annotations

import json
import logging

from .broker import FakeBroker
from .store import WindowStore

log = logging.getLogger("sink")

TOPIC = "vibration.features"
GROUP = "dashboard-sink"
FLUSH_EVERY_POLLS = 5
MAX_BUFFER = 2000

ASSET_TAGS = {f"pump-{i:02d}": f"DUN-P{i:03d}" for i in range(1, 13)}


def enrich(record: dict) -> tuple[str, str, float, str]:
    return (record["device_id"], record["window_start"], float(record["rms"]),
            ASSET_TAGS.get(record["device_id"], "UNKNOWN"))


class Sink:
    def __init__(self, broker: FakeBroker, store: WindowStore) -> None:
        self.store = store
        self.consumer = broker.consumer(GROUP, TOPIC, enable_auto_commit=False)
        self.buffer: list[tuple[str, str, float, str]] = []
        self.polls = 0

    def step(self, max_records: int = 200) -> int:
        msgs = self.consumer.poll(max_records)
        self.polls += 1
        for m in msgs:
            self.buffer.append(enrich(json.loads(m.value)))
        if self.buffer and (self.polls % FLUSH_EVERY_POLLS == 0 or len(self.buffer) >= MAX_BUFFER or not msgs):
            self.flush()
        return len(msgs)

    def flush(self) -> None:
        n = self.store.write_rows(self.buffer)
        # Positions cover exactly what is in the buffer we just wrote: commit them now, never before.
        self.consumer.commit()
        log.info("flush wrote %d rows, committed %s", n, self.consumer.position)
        self.buffer = []
