"""Visible tests: the rendering spec, two checks on fixtures, the estimators, and the
suite's headline result. Hidden tests probe every check with crafted traps."""

from __future__ import annotations

import pytest
from aic1_support import TRANSCRIPTS, T, fixture

from evals.checks import check_checkout_requested, check_chip_limit
from evals.judge import render_transcript
from evals.report import pass_at_k, pass_hat_k, run_suite, summarize
from evals.transcript import load_transcripts


def test_render_transcript_follows_the_spec_exactly():
    t = (
        T().user("Add a  yoga\nmat")
        .call("search_products", {"query": "yoga mat", "filters": {"max_price": 50}})
        .result("Search returned\n1 result")
        .text("Added it.")
        .build()
    )
    assert render_transcript(t) == (
        "USER: Add a yoga mat\n"
        'TOOL_CALL search_products {"filters":{"max_price":50},"query":"yoga mat"}\n'
        "TOOL_RESULT search_products ok: Search returned 1 result\n"
        "ASSISTANT: Added it."
    )


def test_chip_limit_on_recorded_runs():
    assert check_chip_limit(fixture("headphones-compare", 1)).passed
    bad = check_chip_limit(fixture("headphones-compare", 3))
    assert not bad.passed and bad.name == "chip_limit"


def test_checkout_requested_on_recorded_runs():
    assert check_checkout_requested(fixture("checkout-asked", 1)).passed
    assert not check_checkout_requested(fixture("checkout-unasked", 1)).passed


def test_estimators_on_simple_values():
    assert pass_at_k(3, 2, 1) == pytest.approx(2 / 3)
    assert pass_hat_k(3, 2, 2) == pytest.approx(1 / 3)
    assert pass_at_k(3, 0, 3) == 0.0 and pass_hat_k(3, 3, 3) == 1.0


def test_suite_finds_the_always_failing_scenario(judge):
    summary = summarize(run_suite(load_transcripts(TRANSCRIPTS), judge_client=judge), k=2)
    assert summary["runs"] == 30
    assert summary["always_failing"] == ["checkout-unasked"]
    assert summary["judge_errors"] == 0
