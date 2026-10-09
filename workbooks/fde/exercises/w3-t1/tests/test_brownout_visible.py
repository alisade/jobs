"""Visible tests: the deployed config during a brownout. The grader adds hidden tests."""

from __future__ import annotations

from w3t1_support import YOGA_MAT, FakeRisk, deployed_env

from northwind_trust import CHECKOUT_UNAVAILABLE_TEXT, load_policy


def test_deployed_config_means_checkout_fails_closed():
    policy = load_policy(deployed_env())
    assert policy.cart.on_failure == "open"
    assert policy.checkout.on_failure == "closed"


async def test_cart_write_proceeds_when_risk_times_out(make_stack):
    stack = make_stack(deployed_env(), FakeRisk("allow", delay=2.0))
    out = await stack.cart_with_mat()
    assert not out.refused, out.result_text
    assert await stack.cart_ids() == {YOGA_MAT: 1}


async def test_checkout_fails_closed_when_risk_times_out(make_stack):
    stack = make_stack(deployed_env(), FakeRisk("allow"))
    await stack.cart_with_mat()
    stack.risk.delay = 2.0
    out = await stack.executor.execute("checkout", {})
    assert out.is_error, "checkout rendered with no risk decision (fail OPEN)"
    assert out.result_text == CHECKOUT_UNAVAILABLE_TEXT
    assert not [e for e in out.events if e.type == "ui"]
