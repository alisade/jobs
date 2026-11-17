"""Hidden tests for fde/w1-t1: the fixed state, plus the constraints the fix must keep."""

from __future__ import annotations

import json
from datetime import datetime

import pytest
from w1t1_hidden_support import EXERCISE, FLAGS, prefix_in_process

from replay.simulate import WORKER_SEEDS, replay
from storefront_prompt.prompt import build_dynamic_context, build_static_system
from storefront_prompt.request import build_request
from storefront_prompt.specs import TOOL_SPECS
from storefront_prompt.tools import build_tools, enabled_tool_names

# What release 2026.09.29 shipped for these flags (the evals were tuned on this order).
RELEASE_ORDER = [
    "search_products", "get_product_details", "get_cart", "add_to_cart", "update_cart_item",
    "remove_from_cart", "get_preferences", "get_orders", "get_order_status", "search_policies",
    "get_fulfillment_options", "present_products", "present_comparison", "checkout",
    "present_suggestions",
]


def test_tool_order_is_the_previous_release_order():
    assert [t["name"] for t in build_tools(FLAGS)] == RELEASE_ORDER


def test_order_is_stable_across_many_hash_seeds_for_every_flag_combination():
    everything = {"enable_fulfillment": True, "enable_web_search": True, "enable_comparison": True,
                  "extra_tools": ["web_search", "search_products"]}
    for flags in (FLAGS, everything, {"store": "x"}):
        names = {tuple(prefix_in_process(seed, flags)["names"]) for seed in (11, 12, 13, 14, 15)}
        digests = {prefix_in_process(seed, flags)["digest"] for seed in (21, 22, 23)}
        assert len(names) == 1 and len(digests) == 1, flags


def test_one_prefix_across_all_sixteen_replay_workers():
    stats = replay(EXERCISE, FLAGS, datetime(2026, 10, 6, 13, 0), sessions=12)
    distinct = set().union(*stats.prefixes_by_worker.values())
    assert len(stats.prefixes_by_worker) > 1
    assert len(distinct) == 1, f"{len(distinct)} distinct prefixes across {len(WORKER_SEEDS)} workers"


def test_dedupe_still_works():
    flags = dict(FLAGS, extra_tools=["present_comparison", "search_products", "present_comparison"])
    names = enabled_tool_names(flags)
    assert len(names) == len(set(names))
    assert names == RELEASE_ORDER


def test_an_extra_takes_its_release_slot():
    flags = dict(FLAGS, extra_tools=["web_search"])
    names = enabled_tool_names(flags)
    assert names.index("web_search") == names.index("get_fulfillment_options") + 1
    assert names.index("web_search") < names.index("present_products")


def test_unknown_extra_still_fails_fast():
    with pytest.raises(ValueError):
        enabled_tool_names(dict(FLAGS, extra_tools=["delete_account"]))


def test_static_system_lists_tools_in_the_same_order():
    text = build_static_system(FLAGS)
    assert ", ".join(RELEASE_ORDER) in text


def test_build_tools_returns_copies():
    tools = build_tools(FLAGS)
    tools[0]["description"] = "mutated"
    tools[-1]["cache_control"] = {"type": "ephemeral"}
    assert TOOL_SPECS[tools[0]["name"]]["description"] != "mutated"
    assert "cache_control" not in TOOL_SPECS[tools[-1]["name"]]


def test_nothing_per_request_before_the_breakpoint():
    a = build_request(FLAGS, build_dynamic_context(now=datetime(2026, 10, 6, 13, 5), cart_count=0, page="home"),
                      [{"role": "user", "content": "a tent"}])
    b = build_request(FLAGS, build_dynamic_context(now=datetime(2026, 10, 6, 15, 55), cart_count=3, page="cart"),
                      [{"role": "user", "content": "a stove"}])
    assert json.dumps(a["tools"]) == json.dumps(b["tools"])
    assert a["system"][0] == b["system"][0]
    assert a["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "15:00" not in a["system"][0]["text"] and "cart_item_count" not in a["system"][0]["text"]
    marked = [t["name"] for t in a["tools"] if "cache_control" in t]
    assert marked == [a["tools"][-1]["name"]]


def test_hourly_clock_is_not_what_breaks_the_prefix():
    """The red herring: the clock changes the second system block only."""
    early = build_dynamic_context(now=datetime(2026, 10, 6, 13, 1), cart_count=0, page="home")
    late = build_dynamic_context(now=datetime(2026, 10, 6, 13, 59), cart_count=0, page="home")
    assert early == late
