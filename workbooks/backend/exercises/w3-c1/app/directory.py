"""Fake company-directory enrichment (a downstream HTTP call in production: slow and sometimes failing)."""

from __future__ import annotations

import asyncio


class Directory:
    def __init__(self, latency: float = 0.02):
        self.latency = latency
        self.fail_next = 0
        self.gate: asyncio.Event | None = None  # tests can hold requests in flight
        self.calls = 0

    async def lookup(self, domain: str | None) -> dict:
        self.calls += 1
        if self.gate is not None:
            await self.gate.wait()
        await asyncio.sleep(self.latency)
        if self.fail_next:
            self.fail_next -= 1
            raise RuntimeError("directory: upstream 503")
        return {"industry": "Software" if (domain or "").endswith(".io") else "General"}
