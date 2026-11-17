"""vibration.features -> windows table, with asset enrichment and batched writes.

Written for throughput: the enrichment lookup is slow, so records are buffered and
flushed to SQLite every FLUSH_EVERY_POLLS polls (or when the buffer is large).
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
        self.consumer = broker.consumer(GROUP, TOPIC, enable_auto_commit=True, auto_commit_interval_polls=1)
        self.buffer: list[tuple[str, str, float, str]] = []
        self.polls = 0

    def step(self, max_records: int = 200) -> int:
        """One poll; flushes when due. Returns the number of records polled."""
        msgs = self.consumer.poll(max_records)
        self.polls += 1
        for m in msgs:
            self.buffer.append(enrich(json.loads(m.value)))
        if self.buffer and (self.polls % FLUSH_EVERY_POLLS == 0 or len(self.buffer) >= MAX_BUFFER or not msgs):
            self.flush()
        return len(msgs)

    def flush(self) -> None:
        n = self.store.write_rows(self.buffer)
        log.info("flush wrote %d rows", n)
        self.buffer = []
