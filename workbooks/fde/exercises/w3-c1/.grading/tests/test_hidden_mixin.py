"""Hidden tests for fde/w3-c1: the README acceptance criteria past the happy path."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest
from w3c1_hidden_support import SESSION_ID, USER_ID, YOGA_MAT, FakeRisk, TrustedRetail

from trust_mixin import (
    CART_DENIED_TEXT,
    CART_UNAVAILABLE_TEXT,
    CHECKOUT_DENIED_TEXT,
    CHECKOUT_REVIEW_TEXT,
    CHECKOUT_UNAVAILABLE_TEXT,
    REVIEW_GATE,
    TRUST_GATE,
    HookPolicy,
    RiskUnavailable,
    TrustPolicy,
)

HEADPHONES = "AR-1105"


async def _cart_with_mat(stack, quantity=1):
    await stack.seen("yoga mat")
    out = await stack.executor.execute("add_to_cart", {"product_id": YOGA_MAT, "quantity": quantity})
    assert not out.refused, out.result_text


# -- decision mapping -------------------------------------------------------------------


async def test_deny_text_leaks_no_reason_codes_or_decision_ids(make_stack):
    stack = make_stack(FakeRisk("deny", reason_codes=["velocity_high", "device_mismatch"]))
    await stack.seen("yoga mat")
    out = await stack.executor.execute("add_to_cart", {"product_id": YOGA_MAT, "quantity": 1})
    assert out.result_text == CART_DENIED_TEXT
    for leak in ("velocity", "device", "dec-", "Halyard", "score"):
        assert leak not in out.result_text


async def test_cart_review_lets_the_write_through_and_is_logged(make_stack):
    stack = make_stack(FakeRisk("review"))
    await stack.seen("yoga mat")
    out = await stack.executor.execute("add_to_cart", {"product_id": YOGA_MAT, "quantity": 1})
    assert not out.refused
    assert await stack.cart_ids() == {YOGA_MAT: 1}
    assert [r.outcome for r in stack.log] == ["review"]


async def test_checkout_deny_is_held_under_the_trust_gate_with_no_card(make_stack):
    stack = make_stack(FakeRisk("allow"))
    await _cart_with_mat(stack)
    stack.risk.decision = stack.risk.decision.__class__("deny")
    out = await stack.executor.execute("checkout", {})
    assert out.blocked == TRUST_GATE and not out.is_error
    assert out.result_text == CHECKOUT_DENIED_TEXT
    assert not [e for e in out.events if e.type == "ui"]


async def test_checkout_review_is_held_under_the_review_gate(make_stack):
    stack = make_stack(FakeRisk("allow"))
    await _cart_with_mat(stack)
    stack.risk.decision = stack.risk.decision.__class__("review")
    out = await stack.executor.execute("checkout", {})
    assert out.blocked == REVIEW_GATE
    assert out.result_text == CHECKOUT_REVIEW_TEXT
    assert not out.events


# -- fail policy --------------------------------------------------------------------------


async def test_cart_timeout_fails_open_within_the_budget(make_stack):
    stack = make_stack(FakeRisk("deny", delay=2.0))
    await stack.seen("yoga mat")
    started = time.monotonic()
    out = await stack.executor.execute("add_to_cart", {"product_id": YOGA_MAT, "quantity": 1})
    elapsed = time.monotonic() - started
    assert elapsed < 0.6, f"the cart budget is 150 ms; the call took {elapsed:.2f}s"
    assert not out.refused, "a slow risk API must not block a cart write (fail open)"
    assert await stack.cart_ids() == {YOGA_MAT: 1}
    assert stack.log[-1].outcome == "fail_open" and stack.log[-1].error == "TimeoutError"


async def test_checkout_timeout_fails_closed(make_stack):
    stack = make_stack(FakeRisk("allow"))
    await _cart_with_mat(stack)
    stack.risk.delay = 2.0
    started = time.monotonic()
    out = await stack.executor.execute("checkout", {})
    assert time.monotonic() - started < 1.0, "the checkout budget is 400 ms"
    assert out.is_error and out.blocked is None
    assert out.result_text == CHECKOUT_UNAVAILABLE_TEXT
    assert not out.events
    assert stack.log[-1].outcome == "fail_closed"


@pytest.mark.parametrize("error", [RiskUnavailable("503 from risk"), ConnectionError("reset"), ValueError("bad json")])
async def test_client_errors_follow_the_hook_policy(make_stack, error):
    stack = make_stack(FakeRisk("allow", error=error))
    await stack.seen("yoga mat")
    cart = await stack.executor.execute("add_to_cart", {"product_id": YOGA_MAT, "quantity": 1})
    assert not cart.refused, "cart fails open on any client error"
    checkout = await stack.executor.execute("checkout", {})
    assert checkout.is_error and checkout.result_text == CHECKOUT_UNAVAILABLE_TEXT
    assert [r.outcome for r in stack.log] == ["fail_open", "fail_closed"]
    assert all(r.error == type(error).__name__ for r in stack.log)


async def test_policy_is_per_hook_and_configurable(make_stack):
    policy = TrustPolicy(
        cart=HookPolicy(timeout_s=0.05, on_failure="closed"),
        checkout=HookPolicy(timeout_s=0.05, on_failure="open"),
    )
    stack = make_stack(FakeRisk("allow", error=RiskUnavailable("down")), policy)
    await stack.seen("yoga mat")
    cart = await stack.executor.execute("add_to_cart", {"product_id": YOGA_MAT, "quantity": 1})
    assert cart.is_error and cart.blocked is None
    assert cart.result_text == CART_UNAVAILABLE_TEXT
    assert await stack.cart_ids() == {}
    # Seed the cart past the mixin so checkout has something to stage.
    from retail.api.mock_retail import MockRetail

    await MockRetail.add_to_cart(stack.backend, stack.session, YOGA_MAT, 1)
    checkout = await stack.executor.execute("checkout", {})
    assert not checkout.refused, "checkout configured to fail open renders the card"


# -- which hooks are checked --------------------------------------------------------------


async def test_update_checks_only_increases_and_sends_the_delta(make_stack):
    stack = make_stack(FakeRisk("allow"))
    await _cart_with_mat(stack, quantity=2)
    stack.risk.calls.clear()
    out = await stack.executor.execute("update_cart_item", {"product_id": YOGA_MAT, "quantity": 1})
    assert not out.refused and stack.risk.calls == []
    out = await stack.executor.execute("update_cart_item", {"product_id": YOGA_MAT, "quantity": 5})
    assert not out.refused
    assert [(c.hook, c.quantity) for c in stack.risk.calls] == [("update_cart_item", 4)]
    assert await stack.cart_ids() == {YOGA_MAT: 5}


async def test_update_deny_is_held_and_leaves_the_line(make_stack):
    stack = make_stack(FakeRisk("allow"))
    await _cart_with_mat(stack, quantity=1)
    stack.risk.decision = stack.risk.decision.__class__("deny")
    out = await stack.executor.execute("update_cart_item", {"product_id": YOGA_MAT, "quantity": 3})
    assert out.blocked == TRUST_GATE
    assert await stack.cart_ids() == {YOGA_MAT: 1}


async def test_reads_and_removes_never_call_risk(make_stack):
    stack = make_stack(FakeRisk("deny"))
    await stack.seen("yoga mat", "headphones")
    await stack.executor.execute("get_cart", {})
    await stack.executor.execute("get_product_details", {"product_id": HEADPHONES})
    await stack.executor.execute("remove_from_cart", {"product_id": YOGA_MAT})
    assert stack.risk.calls == []


async def test_blueprint_gates_still_run_first(make_stack):
    stack = make_stack(FakeRisk("allow"))
    out = await stack.executor.execute("add_to_cart", {"product_id": YOGA_MAT, "quantity": 1})
    assert out.blocked == "provenance"
    assert stack.risk.calls == [], "an unseen id is held by provenance before any risk call"


# -- privacy and logging --------------------------------------------------------------------


async def test_risk_requests_and_decision_logs_carry_no_raw_identifiers(make_stack):
    stack = make_stack(FakeRisk("allow"))
    await _cart_with_mat(stack)
    await stack.executor.execute("checkout", {})
    assert len(stack.risk.calls) == 2 and len(stack.log) == 2
    for blob in [c.model_dump_json() for c in stack.risk.calls] + [r.model_dump_json() for r in stack.log]:
        assert SESSION_ID not in blob and USER_ID not in blob
    assert stack.risk.calls[0].session_digest == stack.log[0].session_digest
    assert len(stack.risk.calls[0].session_digest) == 16
    assert stack.log[0].decision_id and stack.log[0].latency_ms >= 0


async def test_a_broken_log_sink_does_not_change_the_decision():
    from commerce_common.skills import SkillRegistry
    from shopping_agent import ShoppingAgentConfig, ShoppingSessionContext, ShoppingSessionState
    from trust_mixin import TrustAwareExecutor

    def sink(_record):
        raise OSError("disk full")

    backend = TrustedRetail(risk_client=FakeRisk("allow"), decision_log=sink)
    session = ShoppingSessionContext(session_id="s-1", user_id="u-1")
    ex = TrustAwareExecutor(
        backend=backend, config=ShoppingAgentConfig(), skills=SkillRegistry([]),
        session=session, state=ShoppingSessionState(),
    )
    await ex.execute("search_products", {"query": "yoga mat"})
    out = await ex.execute("add_to_cart", {"product_id": YOGA_MAT, "quantity": 1})
    assert not out.refused, out.result_text


# -- Python mechanics ---------------------------------------------------------------------


async def test_cancellation_propagates_and_is_not_a_fail_open(make_stack):
    stack = make_stack(
        FakeRisk("allow", delay=5.0),
        TrustPolicy(cart=HookPolicy(timeout_s=3.0, on_failure="open")),
    )
    task = asyncio.create_task(stack.backend.add_to_cart(stack.session, YOGA_MAT, 1))
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert await stack.cart_ids() == {}
    assert not [r for r in stack.log if r.outcome == "fail_open"]


def test_cooperative_init_passes_backend_arguments_through():
    import retail.api.mock_retail as mr

    data_dir = Path(mr.__file__).resolve().parents[1] / "data"
    backend = TrustedRetail(data_dir=data_dir, risk_client=FakeRisk())
    assert backend.store_name  # MockRetail.__init__ ran with the passed data_dir
