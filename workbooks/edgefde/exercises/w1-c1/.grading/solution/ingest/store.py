"""SQLite feature store. Idempotent upserts keyed by (device_id, window_start)."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator

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
  temperature_c REAL,
  PRIMARY KEY (device_id, window_start)
);
CREATE TABLE IF NOT EXISTS quarantine (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  reason TEXT NOT NULL,
  raw BLOB NOT NULL,
  UNIQUE (source)
);
"""

UPSERT = """
INSERT INTO features (device_id, window_start, window_s, seq, schema_version, rms, peak, kurtosis, band_energy, temperature_c)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (device_id, window_start) DO UPDATE SET
  window_s=excluded.window_s, seq=excluded.seq, schema_version=excluded.schema_version,
  rms=excluded.rms, peak=excluded.peak, kurtosis=excluded.kurtosis,
  band_energy=excluded.band_energy, temperature_c=excluded.temperature_c
WHERE excluded.seq > features.seq
"""


class FeatureStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self.conn = sqlite3.connect(self.path, isolation_level=None)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield self.conn
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise
        else:
            self.conn.execute("COMMIT")

    @staticmethod
    def _row(r: FeatureRecord) -> tuple:
        dev, ws = r.key
        return (dev, ws, r.window_s, r.seq, r.schema_version, r.rms, r.peak, r.kurtosis,
                json.dumps(r.band_energy), r.temperature_c)

    def write_batch(self, records: Iterable[FeatureRecord], quarantined: Iterable[tuple[bytes, str, str]] = ()) -> int:
        """Upsert records and insert quarantine rows in ONE transaction. Returns rows changed."""
        with self.transaction() as c:
            before = c.total_changes
            c.executemany(UPSERT, [self._row(r) for r in records])
            written = c.total_changes - before
            c.executemany(
                "INSERT OR IGNORE INTO quarantine (source, reason, raw) VALUES (?, ?, ?)",
                [(src, reason, raw) for raw, reason, src in quarantined],
            )
        return written

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
