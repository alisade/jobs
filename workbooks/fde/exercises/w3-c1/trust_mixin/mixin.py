"""AgentTrustMixin: in-path risk checks on the blueprint's cart writes and checkout.

YOUR WORK GOES HERE. Read README.md for the decision matrix and acceptance criteria.

Usage the tests rely on:

    class TrustedRetail(AgentTrustMixin, MockRetail): ...
    backend = TrustedRetail(risk_client=client, trust_policy=TrustPolicy(), decision_log=sink)
    executor = TrustAwareExecutor(backend=backend, config=..., skills=..., session=..., state=...)

Everything the model reads goes through the executor, so the observable contract is the
``ToolOutcome`` that ``executor.execute(...)`` returns for ``add_to_cart``,
``update_cart_item`` and ``checkout``.
"""

from __future__ import annotations

import asyncio  # noqa: F401  (you will need it)
import time  # noqa: F401
from collections.abc import Callable
from typing import Any

from commerce_common.presentation import PresentationRefused  # noqa: F401
from commerce_common.streaming import ToolOutcome
from shopping_agent import Cart, CheckoutHandoff, ShoppingSessionContext
from shopping_agent.executor import ShoppingToolExecutor

from .decisions import (  # noqa: F401
    Decision,
    DecisionRecord,
    Hook,
    RiskClient,
    RiskDecision,
    RiskRequest,
    digest,
)
from .policy import HookPolicy, TrustPolicy  # noqa: F401

TRUST_GATE = "trust"
REVIEW_GATE = "trust_review"

# What the model reads. No reason codes, scores, or vendor names: a fraud signal shown to
# the model can be shown to the customer, and then probed. Use these texts verbatim.
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
        **kwargs: Any,
    ) -> None:
        # TODO: cooperative init. The concrete backend's own arguments (MockRetail takes
        # data_dir=) must still reach it. Keep the three trust arguments on self.
        raise NotImplementedError("AgentTrustMixin.__init__")

    # TODO: one private assessment path used by every hook. It should:
    #   - build a RiskRequest with digests only (decisions.digest), never raw ids
    #   - call the risk client inside the hook's budget (asyncio.timeout)
    #   - treat TimeoutError, RiskUnavailable and any other client exception as a failed
    #     check, resolved by the hook's on_failure policy
    #   - let cancellation propagate (a cancelled turn is not a risk-API outage)
    #   - emit exactly one DecisionRecord per assessment to the decision log

    async def add_to_cart(
        self, session: ShoppingSessionContext, product_id: str, quantity: int
    ) -> Cart:
        # TODO: assess, then write through super() (or refuse per the matrix)
        raise NotImplementedError("add_to_cart")

    async def update_cart_item(
        self, session: ShoppingSessionContext, product_id: str, quantity: int
    ) -> Cart:
        # TODO: assess only when the line grows; the request carries the delta
        raise NotImplementedError("update_cart_item")

    async def checkout_handoff(
        self, session: ShoppingSessionContext, cart: Cart
    ) -> list[CheckoutHandoff]:
        # TODO: assess the whole cart; map deny / review / failure onto the blueprint's
        # presentation refusal (commerce_common.presentation.PresentationRefused)
        raise NotImplementedError("checkout_handoff")


class TrustAwareExecutor(ShoppingToolExecutor):
    """Maps the mixin's cart exceptions onto the blueprint's native results."""

    def domain_error(self, error: Exception) -> ToolOutcome | None:
        # TODO: TrustDenied -> a held result under TRUST_GATE; TrustUnavailable -> an
        # error result. Everything else: the blueprint's own mapping.
        return super().domain_error(error)
