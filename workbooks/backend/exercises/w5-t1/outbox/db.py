"""SQLite stands in for the pipeline-svc Postgres database (the outbox table) and for the consumer's
own database. Same semantics for what matters here: one transaction per call, UPDATE row counts."""

from __future__ import annotations

import json
import sqlite3
import uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS outbox (
  id           INTEGER PRIMARY KEY,
  event_id     TEXT NOT NULL UNIQUE,      -- generated in the same transaction as the business change
  aggregate_id TEXT NOT NULL,             -- opportunity id, used as the Kafka key
  type         TEXT NOT NULL,
  payload      TEXT NOT NULL,
  status       TEXT NOT NULL DEFAULT 'pending',   -- pending | claimed | sent
  claimed_by   TEXT,
  lease_until  REAL,
  created_at   REAL NOT NULL,
  sent_at      REAL
);
CREATE INDEX IF NOT EXISTS outbox_status_idx ON outbox (status, id);
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=10, isolation_level=None)  # autocommit; explicit BEGIN when needed
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_outbox(path: str) -> None:
    conn = connect(path)
    conn.executescript(SCHEMA)
    conn.close()


def add_stage_changes(path: str, n: int, opportunities: int = 20, start: float = 1000.0) -> list[str]:
    """What pipeline-svc writes: one outbox row per stage change, in the change's transaction."""
    conn = connect(path)
    ids = []
    conn.execute("BEGIN")
    versions: dict[str, int] = {}
    for i in range(n):
        opp = f"opp-{i % opportunities:04d}"
        versions[opp] = versions.get(opp, 0) + 1
        eid = str(uuid.UUID(int=(0xA11CE << 96) + i))
        ids.append(eid)
        payload = {"opportunity_id": opp, "version": versions[opp], "to_stage": ["qualification", "proposal",
                   "negotiation", "closed_won"][versions[opp] % 4]}
        conn.execute("INSERT INTO outbox (event_id, aggregate_id, type, payload, created_at) VALUES (?,?,?,?,?)",
                     (eid, opp, "OpportunityStageChanged", json.dumps(payload), start + i))
    conn.execute("COMMIT")
    conn.close()
    return ids
