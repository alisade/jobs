"""timeline-consumer: applies OpportunityStageChanged events to the activity timeline projection.

At-least-once input, so it dedupes on the message's event_id in the same transaction as the effect.
"""

from __future__ import annotations

import sqlite3

from .broker import Broker
from .db import connect

SCHEMA = """
CREATE TABLE IF NOT EXISTS processed_events (event_id TEXT PRIMARY KEY, applied_at REAL);
CREATE TABLE IF NOT EXISTS stage_changes (
  opportunity_id TEXT NOT NULL, version INTEGER NOT NULL, to_stage TEXT NOT NULL, event_id TEXT NOT NULL
);
"""


class Consumer:
    def __init__(self, db_path: str, broker: Broker, group: str = "timeline-consumer") -> None:
        self.db_path, self.broker, self.group = db_path, broker, group
        conn = connect(db_path)
        conn.executescript(SCHEMA)
        conn.close()
        self.applied = 0
        self.skipped = 0

    def poll(self) -> int:
        conn = connect(self.db_path)
        n = 0
        for p in range(self.broker.partitions):
            msgs = self.broker.fetch(self.group, p)
            for m in msgs:
                self._apply(conn, m)
                n += 1
            if msgs:
                self.broker.commit(self.group, p, msgs[-1].offset + 1)
        conn.close()
        return n

    def _apply(self, conn: sqlite3.Connection, m) -> None:
        eid = m.headers["event_id"]
        conn.execute("BEGIN")
        try:
            conn.execute("INSERT INTO processed_events (event_id, applied_at) VALUES (?, 0)", (eid,))
        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK")
            self.skipped += 1
            return
        conn.execute("INSERT INTO stage_changes (opportunity_id, version, to_stage, event_id) VALUES (?,?,?,?)",
                     (m.value["opportunity_id"], m.value["version"], m.value["to_stage"], eid))
        conn.execute("COMMIT")
        self.applied += 1
