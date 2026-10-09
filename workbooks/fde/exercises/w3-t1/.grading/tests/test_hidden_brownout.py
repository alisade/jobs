"""Hidden tests for fde/w3-t1: the fixed state, beyond the visible tests."""

from __future__ import annotations

import time

import pytest
from w3t1_hidden_support import FakeRisk, deployed_env

from northwind_trust import (
    CHECKOUT_UNAVAILABLE_TEXT,
    CircuitBreaker,
    RiskUnavailable,
    load_policy,
)


@pytest.mark.parametrize("raw", ["true", "TRUE", "True", "1", "yes", "YES", " true "])
def test_truthy_strings_mean_fail_open(raw):
    policy = load_policy({"TRUST_CHECKOUT_FAIL_OPEN": raw, "TRUST_CART_FAIL_OPEN": raw})
    assert policy.checkout.on_failure == "open"
    assert policy.cart.on_failure == "open"


@pytest.mark.parametrize("raw", ["false", "FALSE", "False", "0", "no", "No", " false "])
def test_falsy_strings_mean_fail_closed(raw):
    policy = load_policy({"TRUST_CHECKOUT_FAIL_OPEN": raw, "TRUST_CART_FAIL_OPEN": raw})
    assert policy.checkout.on_failure == "closed"
    assert policy.cart.on_failure == "closed"


@pytest.mark.parametrize("raw", ["ture", "2", "disabled", "fasle"])
def test_garbage_is_refused_at_startup(raw):
    with pytest.raises(ValueError):
        load_policy({"TRUST_CHECKOUT_FAIL_OPEN": raw})


def test_garbage_stops_the_backend_from_building():
    from northwind_trust import build_backend

    env = deployed_env() | {"TRUST_CHECKOUT_FAIL_OPEN": "flase"}
    with pytest.raises(ValueError):
        build_backend(env, FakeRisk())


def test_unset_flags_keep_the_documented_defaults():
    policy = load_policy({})
    assert policy.cart.on_failure == "open" and policy.checkout.on_failure == "closed"
    assert policy.cart.timeout_s == pytest.approx(0.15)
    assert policy.checkout.timeout_s == pytest.approx(0.40)


def test_deployed_file_still_parses_every_setting():
    policy = load_policy(deployed_env())
    assert policy.breaker_failures == 5
    assert policy.checkout.timeout_s == pytest.approx(0.40)


async def test_checkout_risk_error_fails_closed_with_the_deployed_config(make_stack):
    stack = make_stack(deployed_env(), FakeRisk("allow"))
    await stack.cart_with_mat()
    stack.risk.error = RiskUnavailable("503")
    out = await stack.executor.execute("checkout", {})
    assert out.is_error and out.result_text == CHECKOUT_UNAVAILABLE_TEXT
    assert stack.log[-1].outcome == "fail_closed" and stack.log[-1].policy == "closed"


async def test_open_breaker_fails_checkout_closed_without_waiting(make_stack):
    breaker = CircuitBreaker(failures=1, reset_s=60)
    breaker.record_failure()
    assert breaker.state == "open"
    stack = make_stack(deployed_env(), FakeRisk("allow", delay=2.0), breaker=breaker)
    await stack.executor.execute("search_products", {"query": "yoga mat"})
    started = time.monotonic()
    cart = await stack.executor.execute("add_to_cart", {"product_id": "AR-1301", "quantity": 1})
    checkout = await stack.executor.execute("checkout", {})
    assert time.monotonic() - started < 0.3, "an open breaker answers without the network"
    assert not cart.refused
    assert checkout.is_error and checkout.result_text == CHECKOUT_UNAVAILABLE_TEXT
    assert [r.error for r in stack.log] == ["BreakerOpen", "BreakerOpen"]
    assert stack.risk.calls == []


async def test_explicit_fail_open_checkout_is_still_honored(make_stack):
    env = deployed_env() | {"TRUST_CHECKOUT_FAIL_OPEN": "true"}
    stack = make_stack(env, FakeRisk("allow"))
    await stack.cart_with_mat()
    stack.risk.delay = 2.0
    out = await stack.executor.execute("checkout", {})
    assert not out.refused, "a deployment may deliberately choose fail-open"


async def test_healthy_checkout_still_renders(make_stack):
    stack = make_stack(deployed_env(), FakeRisk("allow"))
    await stack.cart_with_mat()
    out = await stack.executor.execute("checkout", {})
    assert not out.refused and [e.type for e in out.events] == ["ui"]
