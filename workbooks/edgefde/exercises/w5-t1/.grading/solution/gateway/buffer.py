"""Store-and-forward buffer for alerts and feature summaries (SQLite, WAL).

Everything the gateway produces goes through capture(); replay() drains the buffer to the cloud
whenever the uplink is usable. The buffer is capped: when full, the oldest unsent rows are dropped
and counted, so a long outage cannot fill the gateway's disk.

Fixed: the event id is assigned ONCE, at capture, from the natural key (device, window, kind) and
stored with the row, so every resend of the same event carries the same id and the cloud's
idempotent ingest stores it once. Rows are marked sent per acknowledged id, in one transaction, so
a partial ack or a lost ack never marks unsent rows as sent and never forces a fresh identity.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

from .cloud import AckTimeout, Uplink

log = logging.getLogger("buffer")

SCHEMA = """
CREATE TABLE IF NOT EXISTS pending (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL UNIQUE,
  device_id TEXT NOT NULL,
  window_start TEXT NOT NULL,
  kind TEXT NOT NULL,
  payload TEXT NOT NULL,
  sent INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v INTEGER NOT NULL);
"""


def event_id(device_id: str, window_start: str, kind: str) -> str:
    return f"{device_id}/{window_start}/{kind}"


class Buffer:
    def __init__(self, path: str | Path, max_rows: int = 50_000) -> None:
        self.conn = sqlite3.connect(str(path), isolation_level=None)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)
        self.max_rows = max_rows

    def capture(self, device_id: str, window_start: str, kind: str, payload: dict) -> None:
        self.conn.execute("BEGIN IMMEDIATE")
        self.conn.execute(
            "INSERT OR IGNORE INTO pending (event_id, device_id, window_start, kind, payload) VALUES (?, ?, ?, ?, ?)",
            (event_id(device_id, window_start, kind), device_id, window_start, kind, json.dumps(payload)),
        )
        over = self.pending_count() - self.max_rows
        if over > 0:
            self.conn.execute(
                "DELETE FROM pending WHERE id IN (SELECT id FROM pending WHERE sent = 0 ORDER BY id LIMIT ?)", (over,))
            self.conn.execute("INSERT INTO meta VALUES ('dropped', ?) ON CONFLICT(k) DO UPDATE SET v = v + ?", (over, over))
        self.conn.execute("COMMIT")

    def pending_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM pending WHERE sent = 0").fetchone()[0]

    def dropped(self) -> int:
        row = self.conn.execute("SELECT v FROM meta WHERE k = 'dropped'").fetchone()
        return row[0] if row else 0

    def replay(self, uplink: Uplink, batch: int = 50, max_batches: int = 1000) -> int:
        """Send unsent rows oldest first. Returns rows marked sent. Stops on a link error."""
        sent = 0
        for _ in range(max_batches):
            rows = self.conn.execute(
                "SELECT event_id, device_id, window_start, kind, payload FROM pending WHERE sent = 0 ORDER BY id LIMIT ?",
                (batch,)).fetchall()
            if not rows:
                break
            events = [{"event_id": e, "device_id": d, "window_start": w, "kind": k, "payload": json.loads(p)}
                      for e, d, w, k, p in rows]
            try:
                acked = uplink.send_batch(events)
            except AckTimeout:
                log.warning("ack timeout on batch of %d, resending the same event ids", len(events))
                continue
            except ConnectionError:
                log.info("uplink down, %d rows pending", self.pending_count())
                break
            self.conn.execute("BEGIN IMMEDIATE")
            self.conn.executemany("UPDATE pending SET sent = 1 WHERE event_id = ?", [(a,) for a in acked])
            self.conn.execute("COMMIT")
            sent += len(acked)
            if not acked:
                break
        return sent

    def close(self) -> None:
        self.conn.close()
