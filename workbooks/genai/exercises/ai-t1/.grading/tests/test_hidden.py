"""Hidden checks for genai/ai-t1."""

import datetime as dt
import json

import pytest

from assistant.cost import PRICES, cache_hit_ratio, cost_usd
from assistant.request_builder import build_request, prefix_bytes, prefix_hash
from conftest import NOW, prefix_in_subprocess


def test_prefix_identical_across_worker_processes():
    hashes = {prefix_in_subprocess(seed)["hash"] for seed in ["0", "1", "2", "3", "42", "1001"]}
    assert len(hashes) == 1, f"{len(hashes)} different cache prefixes across worker processes"


def test_tool_order_is_deterministic_and_sorted():
    orders = {tuple(prefix_in_subprocess(seed)["tools"]) for seed in ["7", "8", "9"]}
    assert len(orders) == 1
    names = list(next(iter(orders)))
    assert names == sorted(names)


def test_exactly_one_breakpoint_after_the_static_system_prompt():
    req = build_request("hi", now=NOW)
    marks = [b for b in req["system"] if "cache_control" in b]
    assert len(marks) == 1 and req["system"][-1] is marks[0]
    assert not any("cache_control" in t for t in req["tools"])
    for m in req["messages"]:
        if isinstance(m["content"], list):
            assert not any("cache_control" in b for b in m["content"])


def test_dynamic_data_stays_after_the_breakpoint():
    req = build_request("is store 012 open now?", now=NOW, store_id="087")
    pb = prefix_bytes(req).decode()
    assert "2026-11-12" not in pb and "09:30" not in pb and "087" not in pb
    assert "09:30:15" in req["messages"][-1]["content"]
    assert "087" in req["messages"][-1]["content"]


def test_prefix_ignores_time_store_question_and_history():
    a = build_request("tent?", now=NOW, store_id="012")
    b = build_request("headlamp?", history=[{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}],
                      now=NOW + dt.timedelta(hours=7), store_id="087")
    assert prefix_bytes(a) == prefix_bytes(b)
    assert prefix_hash(a) == prefix_hash(b)


def test_history_order_preserved():
    hist = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
    req = build_request("c", history=hist, now=NOW)
    assert [m["content"] for m in req["messages"][:2]] == ["a", "b"]
    assert req["messages"][-1]["content"].endswith("c")


def test_cost_counts_cache_writes_and_reads():
    usage = {"input_tokens": 200, "cache_creation_input_tokens": 10_000, "cache_read_input_tokens": 0, "output_tokens": 300}
    assert cost_usd(usage) == pytest.approx((200 * 3.00 + 10_000 * 3.75 + 300 * 15.00) / 1e6)
    hit = {"input_tokens": 200, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 10_000, "output_tokens": 300}
    assert cost_usd(hit) == pytest.approx((200 * 3.00 + 10_000 * 0.30 + 300 * 15.00) / 1e6)
    assert cost_usd(hit) < cost_usd(usage)


def test_cost_with_custom_prices_and_missing_fields():
    prices = {"input": 1.0, "cache_write": 2.0, "cache_read": 0.5, "output": 4.0}
    assert cost_usd({"cache_read_input_tokens": 1_000_000}, prices) == pytest.approx(0.5)
    assert cost_usd({}, PRICES) == 0


def test_hit_ratio_guard():
    assert cache_hit_ratio([{"cache_read_input_tokens": 9, "cache_creation_input_tokens": 1}]) == pytest.approx(0.9)
    assert cache_hit_ratio([]) == 0.0


def test_request_is_valid_json_and_keeps_all_tools():
    req = build_request("x", now=NOW)
    json.dumps(req)
    assert len(req["tools"]) == 5
    assert all("input_schema" in t for t in req["tools"])
