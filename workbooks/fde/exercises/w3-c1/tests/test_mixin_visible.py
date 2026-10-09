"""Visible tests: the happy path and the first denial. The grader adds hidden tests for
the rest of the README's acceptance criteria."""

from __future__ import annotations

from w3c1_support import YOGA_MAT, FakeRisk, TrustedRetail

from shopping_agent import StorefrontBackend
from trust_mixin import CART_DENIED_TEXT, TRUST_GATE, AgentTrustMixin


def test_mixin_sits_in_front_of_the_concrete_backend():
    mro = TrustedRetail.__mro__
    assert mro.index(AgentTrustMixin) < mro.index(StorefrontBackend)
    assert issubclass(TrustedRetail, StorefrontBackend)


async def test_allow_passes_through_add_to_cart(make_stack):
    stack = make_stack(FakeRisk("allow"))
    await stack.seen("yoga mat")
    outcome = await stack.executor.execute("add_to_cart", {"product_id": YOGA_MAT, "quantity": 2})
    assert not outcome.refused, outcome.result_text
    assert f"Added {YOGA_MAT} x2" in outcome.result_text
    assert await stack.cart_ids() == {YOGA_MAT: 2}
    assert [c.hook for c in stack.risk.calls] == ["add_to_cart"]
    assert stack.risk.calls[0].product_id == YOGA_MAT and stack.risk.calls[0].quantity == 2


async def test_cart_deny_is_a_held_call_and_nothing_is_written(make_stack):
    stack = make_stack(FakeRisk("deny", reason_codes=["velocity_high"]))
    await stack.seen("yoga mat")
    outcome = await stack.executor.execute("add_to_cart", {"product_id": YOGA_MAT, "quantity": 1})
    assert outcome.blocked == TRUST_GATE
    assert not outcome.is_error
    assert outcome.result_text == CART_DENIED_TEXT
    assert await stack.cart_ids() == {}


async def test_checkout_allow_renders_the_card(make_stack):
    stack = make_stack(FakeRisk("allow"))
    await stack.seen("yoga mat")
    await stack.executor.execute("add_to_cart", {"product_id": YOGA_MAT, "quantity": 1})
    outcome = await stack.executor.execute("checkout", {"note": "check the size"})
    assert not outcome.refused, outcome.result_text
    assert [e.type for e in outcome.events] == ["ui"]
    assert stack.risk.calls[-1].hook == "checkout"
    assert stack.risk.calls[-1].amount == 42.0
