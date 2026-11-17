"""Fake async FHIR evaluation client, instrumented for tests (in-flight count, cancellations)."""

from __future__ import annotations

import asyncio


class FakeFhir:
    def __init__(self, cases=("PA-2026-0001", "PA-2026-0002"), delays=None, failing=(), default_delay=0.01):
        self.cases = set(cases)
        self.delays = dict(delays or {})
        self.failing = set(failing)
        self.default_delay = default_delay
        self.in_flight = 0
        self.max_in_flight = 0
        self.cancelled = 0
        self.completed = 0

    async def case_exists(self, case_id: str) -> bool:
        await asyncio.sleep(0)
        return case_id in self.cases

    async def evaluate(self, case_id: str, criterion: str) -> tuple[bool, str]:
        """Return (met, evidence). Sleeps to simulate FHIR search latency."""
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(self.delays.get(criterion, self.default_delay))
            if criterion in self.failing:
                raise ConnectionError("FHIR store returned 503")
            self.completed += 1
            met = not criterion.endswith("x")
            return met, f"Observation/obs-{abs(hash((case_id, criterion))) % 10000}"
        except asyncio.CancelledError:
            self.cancelled += 1
            raise
        finally:
            self.in_flight -= 1
