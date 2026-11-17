"""Hidden tests for fde/w4-c1: redaction, validation, error results, MRO edge cases."""

from __future__ import annotations

import math
import re

import pytest
from w4c1_hidden_support import GOOD_POLICY, call, client, dumps, raw_store

from trust_advisor.redact import digest, redact_text
from trust_advisor.store import DecisionStore

SAMPLES = "trust_advisor.sample_backends"
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


# -- explain_decision ----------------------------------------------------------------------


async def test_unknown_decision_is_an_error_result():
    async with client() as s:
        is_error, _, text = await call(s, "explain_decision", {"decision_id": "hx-1006-999999"})
    assert is_error and "unknown" in text.lower()


@pytest.mark.parametrize("bad", ["hx-1006-1", "../../etc/passwd", "x" * 100, "hx-1006-000106; DROP", ""])
async def test_malformed_decision_ids_are_rejected(bad):
    async with client() as s:
        is_error, data, text = await call(s, "explain_decision", {"decision_id": bad})
    assert is_error and data is None
    assert "Traceback" not in text


async def test_no_raw_identifier_or_email_ever_leaves_the_server():
    store = raw_store()
    async with client() as s:
        for rec in store.recent(1000):
            is_error, data, text = await call(s, "explain_decision", {"decision_id": rec["decision_id"]})
            assert not is_error, text
            blob = dumps(data) + text
            for field in ("session_id", "customer_email", "client_ip"):
                assert rec[field] not in blob, f"{field} leaked for {rec['decision_id']}"
            assert not EMAIL.search(blob), f"an email address leaked for {rec['decision_id']}"
            assert not re.search(r"\bsess-", blob)
            assert data["session_digest"] == digest(rec["session_id"])


@pytest.mark.parametrize(
    ("decision_id", "present", "absent"),
    [
        ("hx-1006-000102", ["[email]", "4417"], ["jordan.alvarez"]),
        ("hx-1006-000103", ["hx-1006-000117", "[ip]"], ["203.0.113.42"]),
        ("hx-1006-000104", ["[card]"], ["4111 1111"]),
        ("hx-1006-000105", ["[phone]"], ["415-555-0134"]),
        ("hx-1006-000106", ["[email]", "[session]"], ["m.chen", "7f3c9a1e"]),
        ("hx-1006-000108", ["[card]", "[phone]"], ["5500-0000", "555-0199"]),
    ],
)
async def test_analyst_notes_are_redacted_without_destroying_them(decision_id, present, absent):
    async with client() as s:
        _, data, _ = await call(s, "explain_decision", {"decision_id": decision_id})
    note = data["analyst_note"]
    for token in present:
        assert token in note, f"{token!r} missing from {note!r}"
    for token in absent:
        assert token not in note, f"{token!r} still in {note!r}"


async def test_unknown_reason_codes_are_explained_not_errors():
    async with client() as s:
        is_error, data, _ = await call(s, "explain_decision", {"decision_id": "hx-1006-000115"})
    assert not is_error
    codes = {e["code"]: e for e in data["explanations"]}
    assert set(codes) == {"geo_velocity_v2", "velocity_high"}
    assert "not in this catalog" in codes["geo_velocity_v2"]["meaning"]


def test_redact_text_caps_length():
    assert len(redact_text("a" * 5000)) == 500
    assert redact_text("") == ""


# -- validate_policy_config ------------------------------------------------------------------


def _codes(data):
    return {(f["path"], f["code"], f["severity"]) for f in data["findings"]}


async def _lint(text):
    async with client() as s:
        return await call(s, "validate_policy_config", {"yaml_text": text})


async def test_fail_open_checkout_is_an_error():
    _, data, _ = await _lint(GOOD_POLICY.replace("on_failure: closed", "on_failure: open"))
    assert data["valid"] is False
    assert ("checkout.on_failure", "checkout_fail_open", "error") in _codes(data)


async def test_yaml_boolean_on_failure_is_called_out():
    _, data, _ = await _lint(GOOD_POLICY.replace("on_failure: closed", "on_failure: off"))
    assert data["valid"] is False
    assert ("checkout.on_failure", "yaml_boolean", "error") in _codes(data)


async def test_unknown_keys_and_missing_sections():
    text = GOOD_POLICY.replace("checkout:", "chekout:").replace("cart:\n  timeout_ms", "cart:\n  timeout")
    _, data, _ = await _lint(text)
    codes = _codes(data)
    assert ("chekout", "unknown_key", "error") in codes
    assert ("checkout", "missing_section", "warning") in codes
    assert ("cart.timeout", "unknown_key", "error") in codes
    assert data["valid"] is False


@pytest.mark.parametrize("value", ["0", "9000", "fast", "true"])
async def test_out_of_range_budgets_are_invalid(value):
    _, data, _ = await _lint(GOOD_POLICY.replace("timeout_ms: 400", f"timeout_ms: {value}"))
    assert ("checkout.timeout_ms", "invalid_value", "error") in _codes(data)


async def test_high_cart_budget_is_only_a_warning():
    _, data, _ = await _lint(GOOD_POLICY.replace("timeout_ms: 150", "timeout_ms: 400"))
    assert data["valid"] is True
    assert ("cart.timeout_ms", "budget_high", "warning") in _codes(data)


async def test_bad_breaker_values():
    _, data, _ = await _lint(GOOD_POLICY.replace("failures: 5", "failures: 0"))
    assert ("breaker.failures", "invalid_value", "error") in _codes(data)


@pytest.mark.parametrize("text", ["cart: [unclosed", "- a\n- b\n", "just a string", "x: " + "y" * 20000])
async def test_unlintable_input_is_an_error_result(text):
    is_error, data, msg = await _lint(text)
    assert is_error and data is None and "Traceback" not in msg


async def test_yaml_tags_are_never_executed(tmp_path):
    marker = tmp_path / "pwned"
    text = f'cart: !!python/object/apply:builtins.open ["{marker}", "w"]\n'
    is_error, _, _ = await _lint(text)
    assert is_error
    assert not marker.exists(), "yaml.load executed a python tag; use yaml.safe_load"


# -- list_hooks_covered ----------------------------------------------------------------------


async def _hooks(target, **kwargs):
    async with client(**kwargs) as s:
        return await call(s, "list_hooks_covered", {"backend": target})


async def test_misordered_mixin_is_reported():
    is_error, data, _ = await _hooks(f"{SAMPLES}:WrongOrder")
    assert not is_error
    assert data["ok"] is False
    assert data["missing"] == ["add_to_cart", "update_cart_item", "checkout_handoff"]
    assert data["misordered_mixins"] == [f"{SAMPLES}.TrustMixin"]


async def test_cart_only_mixin_misses_checkout():
    _, data, _ = await _hooks(f"{SAMPLES}:CartOnlyTrusted")
    assert data["missing"] == ["checkout_handoff"]
    owner = {h["hook"]: h["defined_by"] for h in data["hooks"]}
    assert owner["checkout_handoff"] == "shopping_agent.backend.StorefrontBackend"
    assert owner["add_to_cart"] == f"{SAMPLES}.CartOnlyTrustMixin"


async def test_backend_override_is_not_mixin_coverage():
    _, data, _ = await _hooks(f"{SAMPLES}:CartOnlyOverHostedCheckout")
    owner = {h["hook"]: (h["defined_by"], h["covered"]) for h in data["hooks"]}
    assert owner["checkout_handoff"] == (f"{SAMPLES}.RetailWithHostedCheckout", False)
    assert data["missing"] == ["checkout_handoff"]
    _, inline, _ = await _hooks(f"{SAMPLES}:InlineTrusted")
    assert {h["hook"]: h["covered"] for h in inline["hooks"]}["add_to_cart"] is False


async def test_stacked_mixins_are_fine():
    _, data, _ = await _hooks(f"{SAMPLES}:StackedTrusted")
    assert data["ok"] is True and data["misordered_mixins"] == []
    assert data["resolution_order"][0] == f"{SAMPLES}.StackedTrusted"
    assert "builtins.object" not in data["resolution_order"]


async def test_plain_blueprint_backend_is_allowed_and_uncovered():
    is_error, data, _ = await _hooks("retail.api.mock_retail:MockRetail")
    assert not is_error and data["ok"] is False and len(data["missing"]) == 3


@pytest.mark.parametrize(
    "target",
    ["os:system", "subprocess:Popen", f"{SAMPLES}_evil:X", "GoodTrusted", "a:b:c", "", "retail.api.nope:X",
     f"{SAMPLES}:NotABackend", f"{SAMPLES}:DoesNotExist"],
)
async def test_bad_targets_are_error_results(target):
    is_error, data, text = await _hooks(target)
    assert is_error and data is None and "Traceback" not in text


async def test_allowed_modules_is_configurable():
    is_error, _, _ = await _hooks(f"{SAMPLES}:GoodTrusted", allowed_modules=("retail.api",))
    assert is_error


# -- decision_stats ---------------------------------------------------------------------------


async def test_stats_match_the_raw_records_for_one_hook():
    rows = raw_store().recent(10, "checkout")
    async with client() as s:
        is_error, data, _ = await call(s, "decision_stats", {"hook": "checkout", "last_n": 10})
    assert not is_error and data["window"] == len(rows) == 10
    expected = {}
    for r in rows:
        expected[r["outcome"]] = expected.get(r["outcome"], 0) + 1
    assert data["counts"] == expected
    assert data["fail_open_rate"] == pytest.approx(expected.get("fail_open", 0) / 10, abs=1e-3)
    lat = sorted(r["latency_ms"] for r in rows)
    assert data["p95_latency_ms"] == lat[math.ceil(0.95 * len(lat)) - 1]


@pytest.mark.parametrize("args", [{"last_n": 0}, {"last_n": 1001}, {"last_n": -5}, {"hook": "checkout_handoff"}])
async def test_stats_input_is_validated(args):
    async with client() as s:
        is_error, data, _ = await call(s, "decision_stats", args)
    assert is_error and data is None


async def test_stats_on_an_empty_store():
    async with client(store=DecisionStore([])) as s:
        is_error, data, _ = await call(s, "decision_stats", {})
    assert not is_error
    assert data["window"] == 0 and data["fail_open_rate"] == 0.0 and data["p95_latency_ms"] == 0
