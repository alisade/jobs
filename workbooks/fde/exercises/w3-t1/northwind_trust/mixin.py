"""AgentTrustMixin as deployed in northwind-trust 1.4.0: in-path risk checks on the
blueprint's cart writes and checkout, behind a circuit breaker."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import Any

from commerce_common.presentation import PresentationRefused
from commerce_common.streaming import ToolOutcome
from shopping_agent import Cart, CheckoutHandoff, ShoppingSessionContext
from shopping_agent.executor import ShoppingToolExecutor

from .decisions import (
    Decision,
    DecisionRecord,
    Hook,
    RiskClient,
    RiskDecision,
    RiskRequest,
    digest,
)
from .breaker import BreakerOpen, CircuitBreaker
from .policy import HookPolicy, TrustPolicy

TRUST_GATE = "trust"
REVIEW_GATE = "trust_review"

# What the model reads. No reason codes, scores, or vendor names: a fraud signal shown to
# the model can be shown to the customer, and then probed.
CART_DENIED_TEXT = (
    "This item cannot be added in this conversation. Tell the customer it is not "
    "available to buy here right now and offer to keep shopping; do not retry the add."
)
CART_UNAVAILABLE_TEXT = (
    "Adding to the cart is temporarily unavailable. Tell the customer and do not retry "
    "this turn."
)
CHECKOUT_DENIED_TEXT = (
    "Checkout cannot be completed in this conversation. Tell the customer to finish in "
    "the app, where the store can help; do not retry."
)
CHECKOUT_REVIEW_TEXT = (
    "This order needs a short verification step in the app before checkout. Tell the "
    "customer; do not retry."
)
CHECKOUT_UNAVAILABLE_TEXT = (
    "Checkout is temporarily unavailable. Tell the customer to try again shortly; do not "
    "retry this turn."
)


class TrustDenied(Exception):
    """A cart write the risk decision refused. The executor maps it to a held result."""


class TrustUnavailable(Exception):
    """A cart write refused because the risk check failed and the cart hook fails closed."""


class AgentTrustMixin:
    """Put it first in the bases: ``class TrustedRetail(AgentTrustMixin, MockRetail)``."""

    def __init__(
        self,
        *args: Any,
        risk_client: RiskClient,
        trust_policy: TrustPolicy | None = None,
        decision_log: Callable[[DecisionRecord], None] | None = None,
        breaker: CircuitBreaker | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._risk = risk_client
        self._trust_policy = trust_policy or TrustPolicy()
        self._decision_log = decision_log
        self._breaker = breaker or CircuitBreaker(
            self._trust_policy.breaker_failures, self._trust_policy.breaker_reset_s
        )

    # -- the one assessment path -----------------------------------------------------

    async def _assess(
        self,
        hook: Hook,
        policy: HookPolicy,
        session: ShoppingSessionContext,
        *,
        product_id: str | None = None,
        quantity: int | None = None,
        amount: float | None = None,
        currency: str = "USD",
    ) -> Decision | None:
        """The decision, or None when the check failed (timeout or client error).
        CancelledError is not a failure: it propagates."""
        request = RiskRequest(
            hook=hook,
            session_digest=digest(session.session_id),
            user_digest=digest(session.user_id),
            product_id=product_id,
            quantity=quantity,
            amount=amount,
            currency=currency,
        )
        started = time.monotonic()
        result: RiskDecision | None = None
        error: str | None = None
        try:
            self._breaker.check()
            async with asyncio.timeout(policy.timeout_s):
                result = await self._risk.assess(request)
        except BreakerOpen:
            error = "BreakerOpen"
        except TimeoutError:
            error = "TimeoutError"
            self._breaker.record_failure()
        except Exception as exc:  # any client failure is a failed check, per policy
            error = type(exc).__name__
            self._breaker.record_failure()
        else:
            self._breaker.record_success()

        if result is None:
            outcome = "fail_open" if policy.on_failure == "open" else "fail_closed"
        else:
            outcome = result.decision.value
        self._log(
            DecisionRecord(
                hook=hook,
                outcome=outcome,
                latency_ms=int((time.monotonic() - started) * 1000),
                session_digest=request.session_digest,
                decision_id=result.decision_id if result else None,
                reason_codes=list(result.reason_codes) if result else [],
                error=error,
                policy=policy.on_failure,
            )
        )
        return result.decision if result else None

    def _log(self, record: DecisionRecord) -> None:
        if self._decision_log is None:
            return
        try:
            self._decision_log(record)
        except Exception:  # a broken log sink must not change a decision
            pass

    async def _check_cart(
        self, hook: Hook, session: ShoppingSessionContext, product_id: str, quantity: int
    ) -> None:
        policy = self._trust_policy.cart
        decision = await self._assess(
            hook, policy, session, product_id=product_id, quantity=quantity
        )
        if decision is None:
            if policy.on_failure == "closed":
                raise TrustUnavailable(CART_UNAVAILABLE_TEXT)
            return
        if decision is Decision.DENY:
            raise TrustDenied(CART_DENIED_TEXT)
        # ALLOW and REVIEW both let a cart write through; review is settled at checkout.

    # -- the hooks -------------------------------------------------------------------

    async def add_to_cart(
        self, session: ShoppingSessionContext, product_id: str, quantity: int
    ) -> Cart:
        await self._check_cart("add_to_cart", session, product_id, quantity)
        return await super().add_to_cart(session, product_id, quantity)  # type: ignore[misc]

    async def update_cart_item(
        self, session: ShoppingSessionContext, product_id: str, quantity: int
    ) -> Cart:
        cart: Cart = await self.get_cart(session)  # type: ignore[attr-defined]
        line = next((i for i in cart.items if i.product_id == product_id), None)
        if line is not None and quantity > line.quantity:
            await self._check_cart(
                "update_cart_item", session, product_id, quantity - line.quantity
            )
        return await super().update_cart_item(session, product_id, quantity)  # type: ignore[misc]

    async def checkout_handoff(
        self, session: ShoppingSessionContext, cart: Cart
    ) -> list[CheckoutHandoff]:
        policy = self._trust_policy.checkout
        decision = await self._assess(
            "checkout", policy, session, amount=cart.subtotal, currency=cart.currency
        )
        if decision is None:
            if policy.on_failure == "closed":
                raise PresentationRefused(CHECKOUT_UNAVAILABLE_TEXT)
        elif decision is Decision.DENY:
            raise PresentationRefused(CHECKOUT_DENIED_TEXT, TRUST_GATE)
        elif decision is Decision.REVIEW:
            raise PresentationRefused(CHECKOUT_REVIEW_TEXT, REVIEW_GATE)
        return await super().checkout_handoff(session, cart)  # type: ignore[misc]


class TrustAwareExecutor(ShoppingToolExecutor):
    """Maps the mixin's cart exceptions onto the blueprint's native results: a denial is a
    held call (status ``blocked``, gate ``trust``), a fail-closed outage an error result."""

    def domain_error(self, error: Exception) -> ToolOutcome | None:
        if isinstance(error, TrustDenied):
            return ToolOutcome.held(TRUST_GATE, CART_DENIED_TEXT)
        if isinstance(error, TrustUnavailable):
            return ToolOutcome.error(CART_UNAVAILABLE_TEXT)
        return super().domain_error(error)
