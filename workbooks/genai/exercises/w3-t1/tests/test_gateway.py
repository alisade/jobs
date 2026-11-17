from conftest import make
from assistant_gateway.provider import Reply


def test_short_answer_from_primary(question):
    gw, provider, _ = make([Reply(output_tokens=150, text="The Basecamp 3P fits three.")])
    c = gw.answer("c-1", question, max_tokens=512)
    assert c.model == "primary"
    assert c.text == "The Basecamp 3P fits three."
    assert len(provider.calls) == 1


def test_successful_attempt_is_logged_with_cost(question):
    gw, _, _ = make([Reply(output_tokens=200)])
    gw.answer("c-2", question, max_tokens=512)
    ok = [a for a in gw.attempt_log if a["outcome"] == "ok"]
    assert len(ok) == 1
    assert ok[0]["output_tokens"] == 200
    assert ok[0]["cost_usd"] > 0
