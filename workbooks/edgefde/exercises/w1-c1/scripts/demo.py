"""Produce one hour of traffic to the fake broker and run your consumer once over it."""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gen import DEVICES, record  # noqa: E402
from ingest.broker import FakeBroker  # noqa: E402
from ingest.consumer import run_until_idle  # noqa: E402
from ingest.store import FeatureStore  # noqa: E402

TOPIC = "vibration.features"

if __name__ == "__main__":
    rng = random.Random(1)
    b = FakeBroker()
    b.create_topic(TOPIC, 3)
    t0 = datetime(2026, 10, 16, 8, tzinfo=timezone.utc)
    for i in range(60):
        for d_i, dev in enumerate(DEVICES):
            r = record(dev, t0 + timedelta(minutes=i), i, rng)
            b.produce(TOPIC, dev.encode(), json.dumps(r).encode())
    b.produce(TOPIC, b"pump-02", b'{"device_id": "pump-02"}')
    db = Path(sys.argv[1] if len(sys.argv) > 1 else "run/demo.db")
    db.parent.mkdir(parents=True, exist_ok=True)
    store = FeatureStore(db)
    res = run_until_idle(b.consumer("features-sink", TOPIC), store)
    print(f"demo: {res}; rows={store.count()} quarantined={store.quarantine_count()} lag={b.lag('features-sink', TOPIC)}")
