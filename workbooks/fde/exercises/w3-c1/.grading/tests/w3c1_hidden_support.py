"""Helpers shared by the visible tests: a scriptable fake risk client and a trusted
retail backend wired into the blueprint's executor."""

from __future__ import annotations

import asyncio
import itertools
from dataclasses import dataclass, field

from retail.api.mock_retail import MockRetail

from commerce_common.skills import SkillRegistry
from shopping_agent import ShoppingAgentConfig, ShoppingSessionContext, ShoppingSessionState
from trust_mixin import (
    AgentTrustMixin,
    Decision,
    DecisionRecord,
    RiskDecision,
    RiskRequest,
    TrustAwareExecutor,
    TrustPolicy,
)

YOGA_MAT = "AR-1301"
SESSION_ID = "sess-7f3c9a1e-raw-session-id"
USER_ID = "demo-user"
_ids = itertools.count(1)


class FakeRisk:
    """Answers ``decision`` after ``delay`` seconds, or raises ``error``."""

    def __init__(self, decision="allow", delay=0.0, error=None, reason_codes=("ok",)):
        self.decision = Decision(decision)
        self.delay = delay
        self.error = error
        self.reason_codes = list(reason_codes)
        self.calls: list[RiskRequest] = []

    async def assess(self, request: RiskRequest) -> RiskDecision:
        self.calls.append(request)
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error is not None:
            raise self.error
        return RiskDecision(
            decision=self.decision, decision_id=f"dec-{next(_ids)}", reason_codes=self.reason_codes
        )


class TrustedRetail(AgentTrustMixin, MockRetail):
    pass


@dataclass
class Stack:
    risk: FakeRisk
    backend: TrustedRetail
    executor: TrustAwareExecutor
    session: ShoppingSessionContext
    log: list[DecisionRecord] = field(default_factory=list)

    async def seen(self, *queries: str) -> None:
        for q in queries:
            await self.executor.execute("search_products", {"query": q})

    async def cart_ids(self) -> dict[str, int]:
        cart = await self.backend.get_cart(self.session)
        return {i.product_id: i.quantity for i in cart.items}


def make_stack(risk: FakeRisk | None = None, policy: TrustPolicy | None = None) -> Stack:
    risk = risk or FakeRisk()
    log: list[DecisionRecord] = []
    backend = TrustedRetail(risk_client=risk, trust_policy=policy, decision_log=log.append)
    session = ShoppingSessionContext(session_id=SESSION_ID, user_id=USER_ID)
    executor = TrustAwareExecutor(
        backend=backend,
        config=ShoppingAgentConfig(),
        skills=SkillRegistry([]),
        session=session,
        state=ShoppingSessionState(),
    )
    return Stack(risk=risk, backend=backend, executor=executor, session=session, log=log)

