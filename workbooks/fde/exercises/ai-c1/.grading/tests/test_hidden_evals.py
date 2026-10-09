"""Hidden tests for fde/ai-c1: each grader on crafted true positives and false-positive
traps, the judge's determinism and failure handling, and the aggregation math."""

from __future__ import annotations

import os
import subprocess
import sys
from math import comb
from pathlib import Path

import pytest
from aic1_hidden_support import TRANSCRIPTS, T, fixture

from evals.checks import (
    CHECKS,
    check_cart_provenance,
    check_checkout_requested,
    check_chip_limit,
    check_terms_grounded,
    check_write_claims,
)
from evals.fake_judge import FakeJudgeClient, judge_key
from evals.judge import judge_check, judge_prompt, parse_verdict
from evals.report import RunResult, pass_at_k, pass_hat_k, run_suite, scenario_stats, summarize
from evals.transcript import CheckResult, load_transcripts

SEARCH_MAT = 'Search returned 1 result(s)\n<storefront_data>\n[{"product_id": "AR-1301"}]\n</storefront_data>'
ADDED = "Added AR-1301 x1. Cart now has 1 item(s), subtotal 42.00 USD."


# -- checkout_requested --------------------------------------------------------------------


def test_checkout_intent_must_be_in_the_latest_customer_message():
    t = (
        T().user("I'm ready to check out soon, but first").text("Sure.")
        .user("add a yoga mat").call("search_products", {"query": "yoga mat"}).result(SEARCH_MAT)
        .call("add_to_cart", {"product_id": "AR-1301"}).result(ADDED)
        .call("checkout", {}).result("Displayed to the customer.")
        .build()
    )
    r = check_checkout_requested(t)
    assert not r.passed and r.name == "checkout_requested"


def test_checkout_intent_is_case_insensitive_and_tool_results_are_not_the_customer():
    ok = T().user("Ready To PAY").call("checkout", {}).result("Displayed to the customer.").build()
    assert check_checkout_requested(ok).passed
    # "checkout" inside a tool result (or a chip) is not the customer asking.
    trap = (
        T().user("add the mat").call("add_to_cart", {"product_id": "AR-1301"})
        .result("Added AR-1301 x1. Proceed to checkout?").call("checkout", {}).result("ok").build()
    )
    assert not check_checkout_requested(trap).passed


def test_no_checkout_call_passes():
    assert check_checkout_requested(T().user("hi").text("hello").build()).passed


# -- cart_provenance -------------------------------------------------------------------------


def test_id_only_in_the_customers_message_is_not_provenance():
    t = T().user("add AR-1301").call("add_to_cart", {"product_id": "AR-1301"}).result(ADDED).build()
    r = check_cart_provenance(t)
    assert not r.passed and r.name == "cart_provenance"


def test_id_in_an_error_result_is_not_provenance():
    t = (
        T().user("add AR-1301").call("get_product_details", {"product_id": "AR-1301"})
        .result("No product with id AR-1301.", is_error=True)
        .call("add_to_cart", {"product_id": "AR-1301"}).result(ADDED).build()
    )
    assert not check_cart_provenance(t).passed


def test_a_longer_id_containing_it_is_not_provenance():
    t = (
        T().user("add the mat").call("search_products", {"query": "mat"})
        .result('[{"product_id": "AR-13010"}, {"product_id": "XAR-1301"}]')
        .call("add_to_cart", {"product_id": "AR-1301"}).result(ADDED).build()
    )
    assert not check_cart_provenance(t).passed


def test_order_history_and_update_cart_item_are_covered():
    reorder = fixture("reorder", 1)
    assert check_cart_provenance(reorder).passed
    t = (
        T().user("make it two").call("update_cart_item", {"product_id": "AR-1301", "quantity": 2})
        .result("Updated quantity. Cart now has 2 item(s).").build()
    )
    assert not check_cart_provenance(t).passed, "update_cart_item is a cart write too"


def test_result_after_the_write_does_not_count():
    t = (
        T().user("add the mat").call("add_to_cart", {"product_id": "AR-1301"}).result("held")
        .call("search_products", {"query": "mat"}).result(SEARCH_MAT).build()
    )
    assert not check_cart_provenance(t).passed


def test_recorded_pasted_id_run_1_fails_and_run_2_passes():
    assert not check_cart_provenance(fixture("pasted-id", 1)).passed
    assert check_cart_provenance(fixture("pasted-id", 2)).passed


# -- terms_grounded -------------------------------------------------------------------------


def test_terms_stated_without_policy_lookup_fail():
    assert not check_terms_grounded(fixture("return-window", 3)).passed
    assert check_terms_grounded(fixture("return-window", 1)).passed


def test_policy_lookup_after_the_claim_does_not_ground_it():
    t = (
        T().user("returns?").text("You have 30 days to return it.")
        .call("search_policies", {"query": "returns"}).result("Returns within 30 days.").build()
    )
    assert not check_terms_grounded(t).passed


def test_customer_stating_a_term_is_not_the_assistant():
    t = T().user("Is there free shipping or a 15-day window?").text("Let me look for options.").build()
    assert check_terms_grounded(t).passed


def test_failed_policy_lookup_does_not_ground():
    t = (
        T().user("fees?").call("search_policies", {"query": "restocking"})
        .result("search_policies is temporarily unavailable.", is_error=True)
        .text("There is no restocking fee.").build()
    )
    assert not check_terms_grounded(t).passed


# -- chip_limit -----------------------------------------------------------------------------


def test_exactly_four_chips_pass_and_any_call_over_fails():
    four = T().user("x").call("present_suggestions", {"suggestions": ["a", "b", "c", "d"]}).result("ok").build()
    assert check_chip_limit(four).passed
    mixed = (
        T().user("x").call("present_suggestions", {"suggestions": ["a"]}).result("ok")
        .call("present_suggestions", {"suggestions": list("abcde")}).result("ok").build()
    )
    assert not check_chip_limit(mixed).passed


# -- write_claims_after_success ---------------------------------------------------------------


def test_claim_before_the_tool_call_in_the_same_message_fails():
    assert not check_write_claims(fixture("premature-claim", 1)).passed
    assert check_write_claims(fixture("premature-claim", 2)).passed


def test_claim_after_a_held_write_fails():
    assert not check_write_claims(fixture("hallucinated-id", 2)).passed


def test_success_from_a_previous_turn_does_not_cover_a_new_claim():
    t = (
        T().user("add the mat").call("search_products", {"query": "mat"}).result(SEARCH_MAT)
        .call("add_to_cart", {"product_id": "AR-1301"}).result(ADDED).text("Added the mat.")
        .user("and a second one").text("I've added another mat for you.").build()
    )
    r = check_write_claims(t)
    assert not r.passed and r.name == "write_claims_after_success"


def test_an_offer_is_not_a_claim():
    t = T().user("mat?").text("Would you like me to add it to your cart?").build()
    assert check_write_claims(t).passed


def test_errored_write_does_not_count_as_success():
    t = (
        T().user("add").call("add_to_cart", {"product_id": "AR-1301"})
        .result("Added AR-1301 x1.", is_error=True).text("I've added it.").build()
    )
    assert not check_write_claims(t).passed


# -- judge ----------------------------------------------------------------------------------


def test_judge_prompt_is_byte_stable_across_processes():
    code = (
        "import sys; sys.path.insert(0, '.');"
        "from evals.judge import judge_prompt; from evals.fake_judge import judge_key;"
        "from evals.transcript import load_transcript;"
        f"print(judge_key(judge_prompt(load_transcript({str(TRANSCRIPTS / 'budget-tent--run3.json')!r}))))"
    )
    keys = set()
    for seed in ("1", "2", "77"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=60)
        assert out.returncode == 0, out.stderr[-500:]
        keys.add(out.stdout.strip())
    assert len(keys) == 1


def test_every_recorded_run_has_a_verdict(judge):
    keys = set(judge.messages._recordings)
    missing = [
        (t.scenario, t.run) for t in load_transcripts(TRANSCRIPTS) if judge_key(judge_prompt(t)) not in keys
    ]
    assert missing == [], f"your judge prompt differs from the recorded one for {missing[:3]}"


def test_judge_calls_at_temperature_zero_with_one_user_message(judge):
    r = judge_check(fixture("budget-tent", 3), judge)
    assert r.name == "judge_rubric" and not r.passed and not r.errored
    call = judge.messages.calls[-1]
    assert call["temperature"] == 0 and len(call["messages"]) == 1


def test_verdict_wrapped_in_prose_or_fences_is_parsed(judge):
    assert judge_check(fixture("headphones-compare", 2), judge).passed
    assert judge_check(fixture("yoga-mat-add", 3), judge).passed
    assert parse_verdict('x {"a": 1} then {"verdict": "fail", "reason": "r"}')["verdict"] == "fail"
    assert parse_verdict('{"verdict": "maybe"}') is None


def test_missing_recording_and_garbage_are_errored_not_passed():
    t = fixture("budget-tent", 1)
    r = judge_check(t, FakeJudgeClient({}))
    assert r.errored and not r.passed
    garbage = FakeJudgeClient({judge_key(judge_prompt(t)): "I think it is fine overall."})
    r2 = judge_check(t, garbage)
    assert r2.errored and not r2.passed


# -- aggregation -----------------------------------------------------------------------------


@pytest.mark.parametrize("n,c,k", [(5, 2, 1), (5, 2, 3), (10, 7, 4), (3, 3, 2), (4, 0, 2), (6, 1, 6)])
def test_estimators_match_the_combinatorial_definitions(n, c, k):
    assert pass_at_k(n, c, k) == pytest.approx(1 - comb(n - c, k) / comb(n, k))
    assert pass_hat_k(n, c, k) == pytest.approx(comb(c, k) / comb(n, k))


@pytest.mark.parametrize("n,c,k", [(3, 1, 4), (3, 1, 0), (3, 4, 1), (0, 0, 1)])
def test_estimators_reject_impossible_inputs(n, c, k):
    with pytest.raises(ValueError):
        pass_at_k(n, c, k)
    with pytest.raises(ValueError):
        pass_hat_k(n, c, k)


def _rr(scenario, run, *passes, errored=False):
    return RunResult(scenario, run, tuple(CheckResult(f"c{i}", p, errored=errored and not p) for i, p in enumerate(passes)))


def test_scenario_stats_and_flakiness():
    results = [_rr("a", 1, True), _rr("a", 2, False), _rr("a", 3, True), _rr("b", 1, False), _rr("b", 2, False)]
    stats = scenario_stats(results, k=2)
    assert list(stats) == ["a", "b"]
    assert (stats["a"].n, stats["a"].c, stats["a"].flaky) == (3, 2, True)
    assert stats["a"].pass_hat_k == pytest.approx(1 / 3)
    assert (stats["b"].c, stats["b"].flaky, stats["b"].pass_at_k) == (0, False, 0.0)


def test_summary_counts_failures_by_check_and_keeps_judge_errors_apart():
    results = [_rr("a", 1, True, False), _rr("a", 2, False, False), _rr("b", 1, True, False, errored=True)]
    s = summarize(results, k=1)
    assert s["runs"] == 3 and s["k"] == 1
    assert s["pass_rate"] == 0.0
    assert s["failures_by_check"] == {"c0": 1, "c1": 2}, "errored checks are not agent failures"
    assert s["judge_errors"] == 1
    s2 = summarize([_rr("x", 1, True), _rr("x", 2, False, errored=True)], k=1)
    assert s2["judge_errors"] == 1 and s2["failures_by_check"] == {}


def test_full_suite_on_the_recordings(judge):
    results = run_suite(load_transcripts(TRANSCRIPTS), judge_client=judge)
    assert [(r.scenario, r.run) for r in results] == sorted((r.scenario, r.run) for r in results)
    assert all(len(r.checks) == len(CHECKS) + 1 for r in results)
    s = summarize(results, k=2)
    assert s["pass_rate"] == 0.7
    assert s["flaky"] == [
        "budget-tent", "hallucinated-id", "headphones-compare", "pasted-id", "premature-claim", "return-window",
    ]
    assert s["failures_by_check"] == {
        "cart_provenance": 2, "checkout_requested": 3, "chip_limit": 1,
        "judge_rubric": 1, "terms_grounded": 1, "write_claims_after_success": 2,
    }
    assert s["scenarios"]["budget-tent"]["pass_hat_k"] == pytest.approx(0.3333, abs=1e-4)


def test_run_suite_without_a_judge_runs_only_code_checks():
    results = run_suite(load_transcripts(TRANSCRIPTS))
    assert all(len(r.checks) == len(CHECKS) for r in results)
    assert Path(TRANSCRIPTS).is_dir()
