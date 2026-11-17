"""outbox-relay: polls pipeline-svc's outbox table and publishes rows to the `pipeline.events` topic.

Runs as 2 replicas. Each poll claims a batch with a lease, publishes it, then marks it sent.
"""

from __future__ import annotations

import json
import time
import uuid
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
        """Claim up to batch_size rows that are pending or whose lease expired."""
        conn = connect(self.db_path)
        now = self.clock()
        rows = conn.execute(
            "SELECT * FROM outbox WHERE status = 'pending' OR (status = 'claimed' AND lease_until < ?) "
            "ORDER BY id LIMIT ?", (now, self.batch_size)).fetchall()
        if rows:
            ids = [r["id"] for r in rows]
            conn.execute(
                f"UPDATE outbox SET status = 'claimed', claimed_by = ?, lease_until = ? "
                f"WHERE id IN ({','.join('?' * len(ids))})", (self.relay_id, now + self.lease_seconds, *ids))
        conn.close()
        return rows

    def publish_claimed(self, rows: list, crash_after: int | None = None) -> int:
        conn = connect(self.db_path)
        done = []
        for n, r in enumerate(rows):
            if crash_after is not None and n == crash_after:
                conn.close()
                raise SimulatedCrash(f"{self.relay_id} killed after {n} messages")
            headers = {"event_id": str(uuid.uuid4()), "type": r["type"], "aggregate_id": r["aggregate_id"]}
            self.broker.publish(r["aggregate_id"], json.loads(r["payload"]), headers)
            self.published += 1
            done.append(r["id"])
        if done:
            conn.execute(f"UPDATE outbox SET status = 'sent', sent_at = ? WHERE id IN ({','.join('?' * len(done))})",
                         (self.clock(), *done))
        conn.close()
        return len(done)

    def run_once(self, crash_after: int | None = None) -> int:
        return self.publish_claimed(self.claim(), crash_after=crash_after)
