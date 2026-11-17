"""In-process stand-in for Kafka (do not edit).

Committed offsets are durable; consumer positions live in memory. With
enable_auto_commit=True the consumer behaves like the Java/librdkafka clients:
at the start of every poll() whose auto-commit interval has elapsed, it commits
the positions reached by the PREVIOUS poll, whether or not your code has done
anything durable with those records yet.
"""

from __future__ import annotations

import logging
import zlib
from dataclasses import dataclass, field

log = logging.getLogger("broker")


@dataclass(frozen=True)
class Message:
    topic: str
    partition: int
    offset: int
    key: bytes
    value: bytes


class FakeBroker:
    def __init__(self) -> None:
        self._logs: dict[str, list[list[Message]]] = {}
        self._committed: dict[tuple[str, str], dict[int, int]] = {}
        self.commit_calls = 0

    def create_topic(self, topic: str, partitions: int = 3) -> None:
        self._logs.setdefault(topic, [[] for _ in range(partitions)])

    def produce(self, topic: str, key: bytes, value: bytes) -> Message:
        parts = self._logs[topic]
        p = zlib.crc32(key) % len(parts)
        m = Message(topic, p, len(parts[p]), key, value)
        parts[p].append(m)
        return m

    def committed(self, group: str, topic: str) -> dict[int, int]:
        return dict(self._committed.get((group, topic), {}))

    def end_offsets(self, topic: str) -> dict[int, int]:
        return {i: len(p) for i, p in enumerate(self._logs[topic])}

    def lag(self, group: str, topic: str) -> int:
        c = self.committed(group, topic)
        return sum(e - c.get(p, 0) for p, e in self.end_offsets(topic).items())

    def consumer(self, group: str, topic: str, enable_auto_commit: bool = True,
                 auto_commit_interval_polls: int = 1) -> "Consumer":
        return Consumer(self, group, topic, enable_auto_commit, auto_commit_interval_polls)

    def _commit(self, group: str, topic: str, offsets: dict[int, int]) -> None:
        self.commit_calls += 1
        self._committed.setdefault((group, topic), {}).update(offsets)


@dataclass
class Consumer:
    broker: FakeBroker
    group: str
    topic: str
    enable_auto_commit: bool = True
    auto_commit_interval_polls: int = 1
    position: dict[int, int] = field(default_factory=dict)
    _since_commit: int = 0

    def __post_init__(self) -> None:
        c = self.broker.committed(self.group, self.topic)
        for p in range(len(self.broker._logs[self.topic])):
            self.position[p] = c.get(p, 0)

    def poll(self, max_records: int = 200) -> list[Message]:
        if self.enable_auto_commit:
            self._since_commit += 1
            if self._since_commit >= self.auto_commit_interval_polls:
                self.broker._commit(self.group, self.topic, dict(self.position))
                log.info("auto-commit group=%s offsets=%s sum=%d", self.group, dict(self.position), sum(self.position.values()))
                self._since_commit = 0
        parts = self.broker._logs[self.topic]
        out: list[Message] = []
        moved = True
        while len(out) < max_records and moved:
            moved = False
            for p, plog in enumerate(parts):
                if len(out) >= max_records:
                    break
                if self.position[p] < len(plog):
                    out.append(plog[self.position[p]])
                    self.position[p] += 1
                    moved = True
        return out

    def commit(self) -> None:
        self.broker._commit(self.group, self.topic, dict(self.position))
