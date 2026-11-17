"""Eligibility client. In production: an async HTTP client to the eligibility service (270/271
behind it). Here: an in-memory fake over synthetic members, with a closed flag for lifespan tests."""

from __future__ import annotations

import asyncio

MEMBERS = {
    "M-100201": {"active": True, "plan_type": "commercial", "plan_tz": "America/New_York"},
    "M-100202": {"active": True, "plan_type": "medicare-advantage", "plan_tz": "America/Chicago"},
    "M-100203": {"active": False, "plan_type": "commercial", "plan_tz": "America/New_York"},
    "M-100204": {"active": True, "plan_type": "medicaid-mco", "plan_tz": "America/Denver"},
    "M-100205": {"active": True, "plan_type": "qhp-ffe", "plan_tz": "America/Phoenix"},
}


class EligibilityClient:
    def __init__(self, delay_s: float = 0.0):
        self.delay_s = delay_s
        self.closed = False
        self.calls = 0

    async def check(self, member_id: str) -> dict:
        if self.closed:
            raise RuntimeError("client is closed")
        self.calls += 1
        if self.delay_s:
            await asyncio.sleep(self.delay_s)
        return MEMBERS.get(member_id, {"active": False, "plan_type": "unknown", "plan_tz": "America/New_York"})

    async def aclose(self) -> None:
        self.closed = True
