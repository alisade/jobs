import json
from pathlib import Path

from lighthouse.bedrock_stub import MIN_TOKENS, FakeConverse
from lighthouse.builder import build_request
from util import TOOLS, Clock, conversation, send, total_cost


def _prefix(req):
    segs = list(req["toolConfig"]["tools"]) + list(req["system"])
    for m in req["messages"]:
        segs += m["content"]
    last = max(i for i, s in enumerate(segs) if "cachePoint" in s)
    return json.dumps(segs[: last + 1], sort_keys=True)


def test_prefix_byte_identical_across_requests():
    a = build_request("lwong", "q1", "req-1", 1794830400.0, TOOLS)
    b = build_request("mchen", "q2", "req-2", 1794830999.0, TOOLS)
    assert _prefix(a) == _prefix(b)


def test_prefix_independent_of_tool_registration_order():
    a = build_request("lwong", "q", "req-1", 1794830400.0, TOOLS)
    b = build_request("lwong", "q", "req-1", 1794830400.0, list(reversed(TOOLS)))
    assert _prefix(a) == _prefix(b)


def test_prefix_large_enough_to_cache():
    req = build_request("lwong", "q", "req-1", 1794830400.0, TOOLS)
    assert len(_prefix(req)) // 4 >= MIN_TOKENS


def test_dynamic_context_still_reaches_the_model():
    req = build_request("lwong", "is my approval still valid?", "req-777", 1794830400.0, TOOLS)
    text = json.dumps(req)
    assert "req-777" in text and "2026-11-16T12:00:00Z" in text and "lwong" in text
    assert "req-777" not in _prefix(req) and "2026-11-16" not in _prefix(req)


def test_question_is_last_user_content():
    req = build_request("lwong", "where is IT-40002?", "req-1", 1794830400.0, TOOLS)
    assert req["messages"][-1]["role"] == "user"
    assert req["messages"][-1]["content"][-1]["text"] == "where is IT-40002?"


def test_history_kept_in_order():
    hist = [{"role": "user", "content": [{"text": "hi"}]}, {"role": "assistant", "content": [{"text": "hello"}]}]
    req = build_request("lwong", "next", "req-2", 1794830400.0, TOOLS, history=hist)
    assert req["messages"][:2] == hist


def test_cost_for_100_conversations_under_budget():
    clock = Clock()
    client = FakeConverse(clock)
    usages = []
    for i in range(100):
        usages += conversation(client, clock, f"user{i % 7}", n_turns=3, start_id=i * 10)
    reads = sum(1 for u in usages if u["cacheReadInputTokens"])
    assert reads >= 295, f"only {reads} of 300 turns read the cache"
    assert total_cost(usages) < 1.2, f"cost {total_cost(usages):.2f} USD for 100 conversations"


def test_answer_names_the_timestamp():
    t = Path("ANSWER.md").read_text().lower()
    assert "cachepoint" in t.replace(" ", "") or "cache point" in t
    assert "timestamp" in t or "current time" in t or "request id" in t
