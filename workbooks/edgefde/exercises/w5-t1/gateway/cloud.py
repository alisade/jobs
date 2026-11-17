"""Fake cloud ingest endpoint and the uplink to it (do not edit).

The ingest API stores events keyed by event_id; a repeated event_id is acknowledged but not stored
twice (that is the platform's documented idempotency contract). The plant WAN link is modelled by
Uplink: it can be down (ConnectionError before anything is sent), and it can lose the response
(AckTimeout AFTER the server has stored some or all of the batch), like a TCP reset on the way back.
The server may also acknowledge only part of a batch (per-request limit), returning the ids it took.
"""

from __future__ import annotations

import random


class AckTimeout(TimeoutError):
    pass


class IngestServer:
    def __init__(self, max_per_request: int = 1000) -> None:
        self.events: dict[str, dict] = {}
        self.order: list[str] = []
        self.received = 0
        self.max_per_request = max_per_request

    def ingest(self, events: list[dict]) -> list[str]:
        acked = []
        for e in events[: self.max_per_request]:
            self.received += 1
            eid = e["event_id"]
            if eid not in self.events:
                self.events[eid] = e
                self.order.append(eid)
            acked.append(eid)
        return acked

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for e in self.events.values():
            out[e["device_id"]] = out.get(e["device_id"], 0) + 1
        return out


class Uplink:
    def __init__(self, server: IngestServer, seed: int = 0) -> None:
        self.server = server
        self.rng = random.Random(seed)
        self.up = True
        self.ack_loss = 0.0      # probability the response is lost after the server stored the batch
        self.partial_loss = 0.0  # probability the connection drops halfway through the batch
        self.calls = 0

    def send_batch(self, events: list[dict]) -> list[str]:
        self.calls += 1
        if not self.up:
            raise ConnectionError("uplink down")
        if events and self.rng.random() < self.partial_loss:
            self.server.ingest(events[: max(1, len(events) // 2)])
            raise AckTimeout("connection reset mid-batch")
        acked = self.server.ingest(events)
        if self.rng.random() < self.ack_loss:
            raise AckTimeout("no response within 10 s")
        return acked
