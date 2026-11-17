"""Hidden checks for genai/w3-t1: no billed-and-discarded retries, bounded attempts and cost."""

import pytest

from conftest import make, question  # noqa: F401  (fixture)
from assistant_gateway.gateway import BudgetExceeded, GatewayError
from assistant_gateway.pricing import cost_usd
from assistant_gateway.provider import InvalidRequest, Overloaded, RateLimited, Reply, Stall


def test_long_answer_completes_in_one_billed_call(question):
    gw, provider, _ = make([Reply(output_tokens=1900)])
    c = gw.answer("c-long", question, max_tokens=2048)
    assert c.output_tokens == 1900
    assert len(provider.calls) == 1, f"{len(provider.calls)} calls for one answer"
    assert len(provider.usage) == 1, "the provider billed more than one generation for one answer"


def test_invalid_request_is_not_retried_or_sent_to_fallback(question):
    gw, provider, _ = make([InvalidRequest("400 prompt is too long")])
    with pytest.raises(GatewayError):
        gw.answer("c-bad", question, max_tokens=512)
    assert len(provider.calls) == 1


def test_rate_limit_honours_retry_after(question):
    gw, provider, _ = make([RateLimited(retry_after=2.0), Reply()])
    c = gw.answer("c-429", question, max_tokens=512)
    assert c.text
    assert len(provider.calls) == 2
    gap = provider.calls[1]["at"] - provider.calls[0]["at"]
    assert gap >= 2.2, f"second call {gap:.2f}s after the first; retry-after was 2s"


def test_overload_retries_back_off(question):
    gw, provider, _ = make([Overloaded(), Reply()])
    gw.answer("c-529", question, max_tokens=512)
    gap = provider.calls[1]["at"] - provider.calls[0]["at"]
    assert gap >= 0.3, f"retried {gap:.2f}s after a 529 (0.2s of that is the failed call): no backoff"


def test_total_attempts_capped_across_primary_and_fallback(question):
    gw, provider, _ = make([Overloaded() for _ in range(20)])
    with pytest.raises(GatewayError):
        gw.answer("c-down", question, max_tokens=512)
    assert len(provider.calls) <= gw.config.max_attempts == 3
    assert {c["model"] for c in provider.calls} == {"primary", "fallback"}


def test_timeout_goes_to_fallback_not_the_same_model(question):
    gw, provider, _ = make([Stall(seconds=300), Reply(text="fallback answer")])
    c = gw.answer("c-stall", question, max_tokens=2048)
    assert [x["model"] for x in provider.calls] == ["primary", "fallback"]
    assert c.text == "fallback answer"


def test_cost_cap_stops_further_attempts(question):
    gw, provider, _ = make([Stall(seconds=300), Stall(seconds=300), Stall(seconds=300)])
    gw.config.max_cost_usd = 0.01
    with pytest.raises(BudgetExceeded):
        gw.answer("c-budget", question, max_tokens=2048)
    assert len(provider.calls) == 1


def test_every_attempt_is_logged_including_discarded(question):
    gw, provider, _ = make([RateLimited(retry_after=1.0), Stall(seconds=300), Reply(output_tokens=300)])
    gw.answer("c-log", question, max_tokens=1024)
    log = [a for a in gw.attempt_log if a["conversation_id"] == "c-log"]
    assert len(log) == len(provider.calls) == 3
    assert [a["discarded"] for a in log] == [True, True, False]
    assert log[1]["outcome"] == "timeout" and log[1]["cost_usd"] > 0, "a timed-out call is still billed"
    ok = log[2]
    assert ok["cost_usd"] == pytest.approx(cost_usd(ok["model"], ok["input_tokens"], 300))


def test_fallback_after_primary_exhausted(question):
    gw, provider, _ = make([Overloaded(), Overloaded(), Reply(text="from fallback")])
    c = gw.answer("c-fb", question, max_tokens=512)
    assert c.text == "from fallback"
    assert provider.calls[-1]["model"] == "fallback"


def test_short_answer_guard(question):
    gw, provider, _ = make([Reply(output_tokens=80, text="Yes, in stock.")])
    assert gw.answer("c-ok", question, max_tokens=256).text == "Yes, in stock."
    assert len(provider.calls) == 1
