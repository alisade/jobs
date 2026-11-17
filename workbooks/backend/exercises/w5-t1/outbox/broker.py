"""An in-process stand-in for Kafka/Redpanda: a topic with partitions, keyed placement, offsets and
consumer-group commits. Publishing is at-least-once from the relay's point of view: a message that was
published stays published, whatever happens to the relay afterwards."""

from __future__ import annotations

import zlib
from dataclasses import dataclass, field


@dataclass
class Message:
    partition: int
    offset: int
    key: str
    value: dict
    headers: dict


@dataclass
class Broker:
    partitions: int = 3
    log: dict[int, list[Message]] = field(default_factory=dict)
    committed: dict[tuple[str, int], int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for p in range(self.partitions):
            self.log.setdefault(p, [])

    def publish(self, key: str, value: dict, headers: dict) -> Message:
        p = zlib.crc32(key.encode()) % self.partitions
        m = Message(p, len(self.log[p]), key, dict(value), dict(headers))
        self.log[p].append(m)
        return m

    def all_messages(self) -> list[Message]:
        return [m for p in sorted(self.log) for m in self.log[p]]

    def fetch(self, group: str, partition: int, max_messages: int = 500) -> list[Message]:
        start = self.committed.get((group, partition), 0)
        return self.log[partition][start:start + max_messages]

    def commit(self, group: str, partition: int, next_offset: int) -> None:
        self.committed[(group, partition)] = next_offset
