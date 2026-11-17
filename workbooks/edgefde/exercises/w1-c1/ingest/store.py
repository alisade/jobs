"""SQLite feature store.

TODO: make writes idempotent, keyed by (device_id, window_start), keeping the
record with the highest seq; write quarantine rows in the same transaction.
The draft below is what the plant's first prototype did: a plain INSERT per row
with autocommit. It duplicates on redelivery and half-writes on a crash.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .models import FeatureRecord

SCHEMA = """
CREATE TABLE IF NOT EXISTS features (
  device_id     TEXT NOT NULL,
  window_start  TEXT NOT NULL,
  window_s      INTEGER NOT NULL,
  seq           INTEGER NOT NULL,
  schema_version INTEGER NOT NULL,
  rms REAL NOT NULL, peak REAL NOT NULL, kurtosis REAL NOT NULL,
  band_energy   TEXT NOT NULL,
  temperature_c REAL
);
CREATE TABLE IF NOT EXISTS quarantine (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  reason TEXT NOT NULL,
  raw BLOB NOT NULL
);
"""


class FeatureStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self.conn = sqlite3.connect(self.path, isolation_level=None)
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def write_batch(self, records: Iterable[FeatureRecord], quarantined: Iterable[tuple[bytes, str, str]] = ()) -> int:
        """Write valid records and quarantine rows (raw, reason, source). Returns rows inserted or changed."""
        n = 0
        for r in records:
            dev, ws = r.key
            self.conn.execute(
                "INSERT INTO features VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (dev, ws, r.window_s, r.seq, r.schema_version, r.rms, r.peak, r.kurtosis,
                 json.dumps(r.band_energy), r.temperature_c),
            )
            n += 1
        for raw, reason, source in quarantined:
            self.conn.execute("INSERT INTO quarantine (source, reason, raw) VALUES (?, ?, ?)", (source, reason, raw))
        return n

    def upsert_many(self, records: Iterable[FeatureRecord]) -> int:
        return self.write_batch(records)

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM features").fetchone()[0]

    def quarantine_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM quarantine").fetchone()[0]

    def quarantine_reasons(self) -> list[str]:
        return [r[0] for r in self.conn.execute("SELECT reason FROM quarantine ORDER BY id")]

    def get(self, device_id: str, window_start: str) -> dict | None:
        cur = self.conn.execute(
            "SELECT device_id, window_start, seq, rms, peak, kurtosis, band_energy, temperature_c, schema_version"
            " FROM features WHERE device_id=? AND window_start=?",
            (device_id, window_start),
        )
        row = cur.fetchone()
        if row is None:
            return None
        keys = ["device_id", "window_start", "seq", "rms", "peak", "kurtosis", "band_energy", "temperature_c", "schema_version"]
        d = dict(zip(keys, row))
        d["band_energy"] = json.loads(d["band_energy"])
        return d

    def count_for_day(self, day: str) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM features WHERE substr(window_start, 1, 10) = ?", (day,)
        ).fetchone()[0]
