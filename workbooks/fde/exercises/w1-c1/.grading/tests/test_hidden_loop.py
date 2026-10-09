"""Hidden tests for fde/w1-c1."""

from __future__ import annotations

import copy
import json
import time

from w1c1_hidden_support import STATIC, TOOLS, SlowExecutor, dynamic, tool_results

from agent_loop import build_request, load_script, run_turn


def _prefix(request):
    """The cached span up to the system breakpoint: tools then the static system block."""
    return json.dumps(request["tools"], sort_keys=True) + json.dumps(request["system"][0], sort_keys=True)


# -- request layout -------------------------------------------------------------------------


def test_exactly_two_breakpoints_and_callers_tools_untouched():
    tools = copy.deepcopy(TOOLS)
    before = json.dumps(tools)
    req = build_request(model="m", static_system=STATIC, dynamic_context="ctx", tools=tools,
                        messages=[{"role": "user", "content": "x"}])
    assert json.dumps(tools) == before, "the caller's tool dicts were modified"
    marked = [t["name"] for t in req["tools"] if "cache_control" in t]
    assert marked == [tools[-1]["name"]]
    assert [b.get("cache_control") for b in req["system"]] == [{"type": "ephemeral"}, None]
    assert [t["name"] for t in req["tools"]] == [t["name"] for t in tools], "tool order must not change"


def test_tool_choice_only_when_given():
    req = build_request(model="m", static_system="s", dynamic_context="d", tools=TOOLS,
                        messages=[{"role": "user", "content": "x"}], tool_choice={"type": "none"})
    assert req["tool_choice"] == {"type": "none"}
    assert req["max_tokens"] > 0 and req["model"] == "m"


# -- the loop --------------------------------------------------------------------------------


async def test_tool_results_answer_in_tool_use_order_even_when_finishing_out_of_order(make_rig):
    rig = make_rig("yoga_mat_parallel")
    slow = SlowExecutor(rig.executor, {"search_products": 0.0})
    # First tool_use (yoga mat) is slow, the second fast: completion order is reversed.
    calls = []

    class Reorder:
        async def execute(self, name, tool_input):
            import asyncio

            if tool_input.get("query") == "yoga mat":
                await asyncio.sleep(0.15)
            calls.append(tool_input.get("query") or name)
            return await slow.execute(name, tool_input)

    await run_turn(rig.client, Reorder(), **rig.kwargs())
    results = tool_results(rig.client.requests[1])
    assert [r["tool_use_id"] for r in results] == ["toolu_01A1", "toolu_01A2"]
    assert calls[:2] == ["headphones", "yoga mat"], "tools did not run concurrently"
    assert "ACME Fit 6mm" in results[0]["content"]


async def test_parallel_tools_run_concurrently(make_rig):
    rig = make_rig("yoga_mat_parallel")
    slow = SlowExecutor(rig.executor, {"search_products": 0.3, "get_product_details": 0.3, "add_to_cart": 0.3})
    started = time.monotonic()
    await run_turn(rig.client, slow, **rig.kwargs())
    assert time.monotonic() - started < 1.0, "two rounds of two 0.3s tools should take ~0.6s"


async def test_is_error_reaches_the_model_and_it_recovers(make_rig):
    rig = make_rig("bad_id_recovery")
    result = await run_turn(rig.client, rig.executor, **rig.kwargs())
    first = tool_results(rig.client.requests[1])
    assert first[0]["tool_use_id"] == "toolu_01C1" and first[0]["is_error"] is True
    assert "AR-99999" in first[0]["content"]
    second = tool_results(rig.client.requests[2])
    assert second[0].get("is_error", False) is False
    assert result.stop_reason == "end_turn" and result.rounds == 3


async def test_held_outcome_is_not_an_error(make_rig):
    rig = make_rig("held_add")
    result = await run_turn(rig.client, rig.executor, **rig.kwargs())
    held = tool_results(rig.client.requests[1])[0]
    assert held.get("is_error", False) is False, "a provenance hold is a normal result, not is_error"
    assert "was not returned by catalog" in held["content"]
    assert result.rounds == 4
    cart = await rig.backend.get_cart(rig.session)
    assert [i.product_id for i in cart.items] == ["AR-1105"]


async def test_events_are_collected_for_the_host(make_rig):
    rig = make_rig("yoga_mat_parallel")
    result = await run_turn(rig.client, rig.executor, **rig.kwargs())
    assert [e.type for e in result.events] == ["cart_update"]


async def test_iteration_cap_forces_a_final_round_without_tools_but_keeps_them(make_rig):
    rig = make_rig("runaway")
    result = await run_turn(rig.client, rig.executor, **rig.kwargs(max_iterations=3))
    assert result.rounds == 4
    assert result.final_text == "This store does not seem to carry tents."
    reqs = rig.client.requests
    assert all("tool_choice" not in r for r in reqs[:3])
    assert reqs[3]["tool_choice"] == {"type": "none"}
    assert _prefix(reqs[3]) == _prefix(reqs[0]), "the forced round must keep the cached prefix (same tools)"


async def test_cap_of_one(make_rig):
    script = load_script("runaway")
    rig = make_rig([script[0], script[3]])
    result = await run_turn(rig.client, rig.executor, **rig.kwargs(max_iterations=1))
    assert result.rounds == 2 and rig.client.requests[1]["tool_choice"] == {"type": "none"}


async def test_usage_sums_all_four_fields(make_rig):
    rig = make_rig("yoga_mat_parallel")
    result = await run_turn(rig.client, rig.executor, **rig.kwargs())
    assert result.usage == {
        "input_tokens": 912 + 377 + 301,
        "output_tokens": 141 + 96 + 58,
        "cache_read_input_tokens": 0 + 6188 + 7648,
        "cache_creation_input_tokens": 6188 + 1460 + 622,
    }


async def test_max_tokens_stop_ends_the_turn(make_rig):
    rig = make_rig([{"content": [{"type": "text", "text": "The mats we carry are"}],
                     "stop_reason": "max_tokens", "usage": {"input_tokens": 5}}])
    result = await run_turn(rig.client, rig.executor, **rig.kwargs())
    assert result.rounds == 1 and result.stop_reason == "max_tokens"
    assert result.final_text == "The mats we carry are"


async def test_callers_history_is_not_mutated_and_is_carried_forward(make_rig):
    rig = make_rig("yoga_mat_parallel")
    history = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": [{"type": "text", "text": "Hi."}]}]
    snapshot = copy.deepcopy(history)
    result = await run_turn(rig.client, rig.executor, **rig.kwargs(messages=history, user_text="mat please"))
    assert history == snapshot
    assert result.messages[:2] == snapshot
    assert rig.client.requests[0]["messages"][-1] == {"role": "user", "content": "mat please"}


async def test_static_prefix_is_byte_stable_across_rounds_and_turns(make_rig):
    rig = make_rig("yoga_mat_parallel")
    first = await run_turn(rig.client, rig.executor, **rig.kwargs(dynamic_context=dynamic("home")))
    rig.client.script.extend(load_script("bad_id_recovery"))
    await run_turn(rig.client, rig.executor,
                   **rig.kwargs(messages=first.messages, user_text="another mat?", dynamic_context=dynamic("cart")))
    prefixes = {_prefix(r) for r in rig.client.requests}
    assert len(prefixes) == 1, "the tools + static system bytes changed between calls"
    assert {r["system"][1]["text"] for r in rig.client.requests} == {dynamic("home"), dynamic("cart")}
