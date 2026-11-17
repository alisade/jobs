"""In-process stand-in for a Kafka cluster (complete: do not edit).

Semantics follow Kafka closely enough for this exercise:

* A topic has N partitions; a record's partition is crc32(key) % N, so one device
  always lands on one partition and keeps its order there.
* A consumer group has *committed* offsets (durable, survive a crash) and each
  consumer instance has a *position* (in memory). ``poll`` returns records from
  the position and advances it. ``commit()`` stores the current positions as the
  group's committed offsets, i.e. "everything before here is done".
* A crash is modelled by throwing the consumer away and calling
  ``broker.consumer(...)`` again: the new instance starts from the committed
  offsets, so anything polled but not committed is delivered again
  (at-least-once delivery).
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Message:
    topic: str
    partition: int
    offset: int
    key: bytes
    value: bytes


@dataclass
class _Topic:
    partitions: list[list[Message]]


class FakeBroker:
    def __init__(self) -> None:
        self._topics: dict[str, _Topic] = {}
        self._committed: dict[tuple[str, str], dict[int, int]] = {}

    def create_topic(self, topic: str, partitions: int = 3) -> None:
        if topic not in self._topics:
            self._topics[topic] = _Topic([[] for _ in range(partitions)])

    def produce(self, topic: str, key: bytes, value: bytes) -> Message:
        t = self._topics[topic]
        p = zlib.crc32(key) % len(t.partitions)
        msg = Message(topic, p, len(t.partitions[p]), key, value)
        t.partitions[p].append(msg)
        return msg

    def end_offsets(self, topic: str) -> dict[int, int]:
        return {i: len(p) for i, p in enumerate(self._topics[topic].partitions)}

    def committed(self, group: str, topic: str) -> dict[int, int]:
        return dict(self._committed.get((group, topic), {}))

    def lag(self, group: str, topic: str) -> int:
        c = self.committed(group, topic)
        return sum(end - c.get(p, 0) for p, end in self.end_offsets(topic).items())

    def consumer(self, group: str, topic: str) -> "Consumer":
        return Consumer(self, group, topic)

    # used by Consumer
    def _commit(self, group: str, topic: str, offsets: dict[int, int]) -> None:
        cur = self._committed.setdefault((group, topic), {})
        cur.update(offsets)


@dataclass
class Consumer:
    broker: FakeBroker
    group: str
    topic: str
    position: dict[int, int] = field(default_factory=dict)
    polls: int = 0

    def __post_init__(self) -> None:
        committed = self.broker.committed(self.group, self.topic)
        for p in range(len(self.broker._topics[self.topic].partitions)):
            self.position[p] = committed.get(p, 0)

    def poll(self, max_records: int = 500) -> list[Message]:
        """Return up to max_records, round-robin over partitions, in offset order per partition."""
        self.polls += 1
        parts = self.broker._topics[self.topic].partitions
        out: list[Message] = []
        progressed = True
        while len(out) < max_records and progressed:
            progressed = False
            for p, log in enumerate(parts):
                if len(out) >= max_records:
                    break
                pos = self.position[p]
                if pos < len(log):
                    out.append(log[pos])
                    self.position[p] = pos + 1
                    progressed = True
        return out

    def commit(self) -> None:
        """Commit the current positions (everything returned by poll so far)."""
        self.broker._commit(self.group, self.topic, dict(self.position))
