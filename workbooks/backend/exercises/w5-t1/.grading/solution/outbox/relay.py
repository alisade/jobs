"""outbox-relay: polls pipeline-svc's outbox table and publishes rows to the `pipeline.events` topic.

Runs as 2 replicas. Delivery is at-least-once by design; what the relay guarantees is:
- every message carries the outbox row's event_id, so a redelivered row is recognizable downstream;
- a claim is one conditional UPDATE ... RETURNING, so two replicas never claim the same live row;
- each row is marked sent right after it is published, and only while this relay still owns it, so a
  crash republishes at most the one in-flight row and an expired lease stops the old owner.
"""

from __future__ import annotations

import json
import time
from typing import Callable

from .broker import Broker
from .db import connect


class SimulatedCrash(Exception):
    """Stands in for SIGKILL (pod killed after the termination grace period)."""


class Relay:
    def __init__(self, db_path: str, broker: Broker, relay_id: str, clock: Callable[[], float] = time.time,
                 batch_size: int = 100, lease_seconds: float = 30.0) -> None:
        self.db_path, self.broker, self.relay_id, self.clock = db_path, broker, relay_id, clock
        self.batch_size, self.lease_seconds = batch_size, lease_seconds
        self.published = 0

    def claim(self) -> list:
        """Atomically claim up to batch_size rows that are pending or whose lease expired."""
        conn = connect(self.db_path)
        now = self.clock()
        rows = conn.execute(
            "UPDATE outbox SET status = 'claimed', claimed_by = ?, lease_until = ? "
            "WHERE id IN (SELECT id FROM outbox WHERE status = 'pending' "
            "             OR (status = 'claimed' AND lease_until < ?) ORDER BY id LIMIT ?) "
            "RETURNING *", (self.relay_id, now + self.lease_seconds, now, self.batch_size)).fetchall()
        conn.close()
        return sorted(rows, key=lambda r: r["id"])

    def _still_owned(self, conn, row_id: int) -> bool:
        r = conn.execute("SELECT 1 FROM outbox WHERE id = ? AND status = 'claimed' AND claimed_by = ? "
                         "AND lease_until >= ?", (row_id, self.relay_id, self.clock())).fetchone()
        return r is not None

    def publish_claimed(self, rows: list, crash_after: int | None = None) -> int:
        conn = connect(self.db_path)
        sent = 0
        try:
            for n, r in enumerate(rows):
                if crash_after is not None and n == crash_after:
                    raise SimulatedCrash(f"{self.relay_id} killed after {n} messages")
                if not self._still_owned(conn, r["id"]):
                    break  # lease lost: another replica owns the rest of this batch now
                headers = {"event_id": r["event_id"], "type": r["type"], "aggregate_id": r["aggregate_id"]}
                self.broker.publish(r["aggregate_id"], json.loads(r["payload"]), headers)
                self.published += 1
                conn.execute("UPDATE outbox SET status = 'sent', sent_at = ? WHERE id = ? AND claimed_by = ?",
                             (self.clock(), r["id"], self.relay_id))
                sent += 1
        finally:
            conn.close()
        return sent

    def run_once(self, crash_after: int | None = None) -> int:
        return self.publish_claimed(self.claim(), crash_after=crash_after)
