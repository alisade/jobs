"""Session records and the per-customer rate limiter, both backed by Redis in prod.
Here an in-process stand-in with the same round-trip latency."""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass


def digest(value: str) -> str:
    return hashlib.sha256(f"larkspur:{value}".encode()).hexdigest()[:12]


def session_id_for(principal: str) -> str:
    """One storefront session per customer: the cart, provenance and memory key."""
    return f"gw-{digest(principal)}"


@dataclass
class SessionRecord:
    principal: str
    session_id: str
    loaded_at: float


class SessionStore:
    """Read-through cache in front of the session table. TTL raised to 900 s in
    release 2026.10.07 to cut Redis load."""

    def __init__(self, latency_s: float, ttl_s: float) -> None:
        self._latency = latency_s
        self._ttl = ttl_s
        self._cache: dict[str, SessionRecord] = {}

    async def load(self, principal: str) -> SessionRecord:
        hit = self._cache.get(principal)
        if hit is not None and time.monotonic() - hit.loaded_at < self._ttl:
            return hit
        await asyncio.sleep(self._latency)  # GET session:<principal>
        record = SessionRecord(principal, session_id_for(principal), time.monotonic())
        self._cache[principal] = record
        return record


class RateLimiter:
    """INCR + EXPIRE per customer per minute."""

    def __init__(self, latency_s: float, per_minute: int = 600) -> None:
        self._latency = latency_s
        self._per_minute = per_minute
        self._counts: dict[str, int] = {}

    async def hit(self, principal: str) -> bool:
        await asyncio.sleep(self._latency)  # INCR rl:<principal>
        self._counts[principal] = self._counts.get(principal, 0) + 1
        return self._counts[principal] <= self._per_minute
