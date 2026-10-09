"""Helpers shared by the visible tests: fake risk clients and the deployed wiring."""

from __future__ import annotations

import asyncio
import itertools
from pathlib import Path

from northwind_trust import (
    Decision,
    RiskDecision,
    RiskRequest,
    build_backend,
    build_executor,
    read_env_file,
)

ROOT = Path(__file__).resolve().parents[1]
DEPLOYED_ENV = ROOT / "deploy" / "trust.env"
YOGA_MAT = "AR-1301"
_ids = itertools.count(1)


class FakeRisk:
    def __init__(self, decision="allow", delay=0.0, error=None):
        self.decision = Decision(decision)
        self.delay = delay
        self.error = error
        self.calls: list[RiskRequest] = []

    async def assess(self, request: RiskRequest) -> RiskDecision:
        self.calls.append(request)
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error is not None:
            raise self.error
        return RiskDecision(decision=self.decision, decision_id=f"hx-{next(_ids)}", reason_codes=["ok"])


def deployed_env() -> dict[str, str]:
    return read_env_file(DEPLOYED_ENV)


class Stack:
    def __init__(self, env, risk, breaker=None):
        self.log = []
        self.risk = risk
        self.backend = build_backend(env, risk, decision_log=self.log.append, breaker=breaker)
        self.executor = build_executor(self.backend, session_id="sess-raw-1", user_id="demo-user")

    async def cart_with_mat(self):
        await self.executor.execute("search_products", {"query": "yoga mat"})
        return await self.executor.execute("add_to_cart", {"product_id": YOGA_MAT, "quantity": 1})

    async def cart_ids(self):
        cart = await self.backend.get_cart(self.executor._session)
        return {i.product_id: i.quantity for i in cart.items}
