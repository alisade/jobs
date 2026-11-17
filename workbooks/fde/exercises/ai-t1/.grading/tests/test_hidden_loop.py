"""Hidden tests for fde/ai-t1: the fixed turn loop answers every tool_use."""

from __future__ import annotations

import asyncio
import copy
import time

import anthropic
import pytest
from ait1_hidden_fakeapi import FakeAnthropic
from ait1_hidden_support import (
    SECRET_HOST,
    ScriptedTools,
    final,
    recorded_turns,
    results_after,
    run,
    text,
    tool_round,
    use,
)

from agentloop import loop
from agentloop.tools import ReplayToolBox

PARALLEL = tool_round(
    text("Checking stock and delivery."),
    use("toolu_a", "check_stock", sku="LH-2201"),
    use("toolu_b", "shipping_estimate", sku="LH-2201"),
)


async def test_every_recorded_turn_completes_with_its_recorded_answer():
    bad = []
    for record in recorded_turns():
        client = FakeAnthropic(copy.deepcopy(record["script"]), set(record["rate_limit_calls"]))
        messages = copy.deepcopy(record["history"])
        try:
            result = await loop.run_turn(
                client, ReplayToolBox(record["tools"]), messages, turn_id=record["turn_id"],
                tool_timeout_s=0.1, retry_base_s=0.001,
            )
            if result.text != record["final_text"]:
                bad.append((record["turn_id"], "wrong final text"))
        except Exception as exc:
            bad.append((record["turn_id"], f"{type(exc).__name__}: {str(exc)[:120]}"))
    assert bad == []


async def test_a_failing_parallel_tool_gets_an_is_error_result():
    tools = ScriptedTools({
        "check_stock": {"error": RuntimeError("boom")},
        "shipping_estimate": {"output": "Oct 13-15"},
    })
    result, client = await run([PARALLEL, final("Delivery Oct 13-15; stock check unavailable.")], tools)
    assert result.text.startswith("Delivery")
    blocks = results_after(client, 0)
    by_id = {b["tool_use_id"]: b for b in blocks}
    assert set(by_id) == {"toolu_a", "toolu_b"}
    assert by_id["toolu_a"].get("is_error") is True and by_id["toolu_a"]["content"]
    assert not by_id["toolu_b"].get("is_error") and by_id["toolu_b"]["content"] == "Oct 13-15"


async def test_a_timed_out_tool_is_an_error_result_and_the_budget_holds():
    tools = ScriptedTools({
        "check_stock": {"delay": 5.0, "output": "late"},
        "shipping_estimate": {"output": "Oct 13-15"},
    })
    started = time.monotonic()
    result, client = await run([PARALLEL, final()], tools, tool_timeout_s=0.1)
    assert time.monotonic() - started < 1.5
    blocks = results_after(client, 0)
    assert [b["tool_use_id"] for b in blocks] == ["toolu_a", "toolu_b"]
    assert blocks[0].get("is_error") is True and "late" not in str(blocks[0]["content"])


async def test_results_follow_tool_use_order_not_completion_order():
    script = [
        tool_round(
            use("toolu_1", "search_catalog", query="lamp"),
            use("toolu_2", "check_stock", sku="LH-2201"),
            use("toolu_3", "shipping_estimate", sku="LH-2201"),
        ),
        final(),
    ]
    tools = ScriptedTools({
        "search_catalog": {"delay": 0.15, "output": "s"},
        "check_stock": {"delay": 0.05, "output": "c"},
        "shipping_estimate": {"output": "e"},
    })
    _, client = await run(script, tools)
    assert [b["tool_use_id"] for b in results_after(client, 0)] == ["toolu_1", "toolu_2", "toolu_3"]


async def test_tool_results_come_first_one_per_tool_use():
    tools = ScriptedTools({"check_stock": {"output": "4"}, "shipping_estimate": {"output": "Oct"}})
    _, client = await run([PARALLEL, final()], tools)
    blocks = results_after(client, 0)
    assert all(b["type"] == "tool_result" for b in blocks), "tool_result blocks must lead (and here, be all)"
    assert len(blocks) == 2


async def test_a_single_failing_tool_does_not_send_an_empty_message():
    script = [tool_round(use("toolu_s", "check_stock", sku="LH-2201")), final("Stock unavailable.")]
    tools = ScriptedTools({"check_stock": {"error": ConnectionError("reset")}})
    result, client = await run(script, tools)
    assert result.text == "Stock unavailable."
    blocks = results_after(client, 0)
    assert len(blocks) == 1 and blocks[0]["is_error"] is True


async def test_every_tool_failing_still_finishes_the_turn():
    tools = ScriptedTools({
        "check_stock": {"error": RuntimeError("a")},
        "shipping_estimate": {"error": TimeoutError("b")},
    })
    result, client = await run([PARALLEL, final("Neither check is available right now.")], tools)
    assert result.text.startswith("Neither")
    assert [b.get("is_error") for b in results_after(client, 0)] == [True, True]


async def test_an_unknown_tool_name_is_an_error_result():
    script = [tool_round(use("toolu_x", "apply_coupon", code="SAVE10")), final("I cannot apply coupons.")]
    result, client = await run(script, ScriptedTools({}))
    assert result.text == "I cannot apply coupons."
    assert results_after(client, 0)[0]["is_error"] is True


async def test_error_results_do_not_leak_exception_text_to_the_model():
    tools = ScriptedTools({
        "check_stock": {"error": RuntimeError(f"{SECRET_HOST} read timed out (pool inv-ro-3)")},
        "shipping_estimate": {"output": "Oct"},
    })
    _, client = await run([PARALLEL, final()], tools)
    sent = str(results_after(client, 0))
    assert SECRET_HOST not in sent and "inv-ro-3" not in sent


async def test_rate_limit_retries_still_work():
    tools = ScriptedTools({"check_stock": {"output": "4"}, "shipping_estimate": {"output": "Oct"}})
    result, client = await run([PARALLEL, final("ok")], tools, rate_limit_calls={0, 2})
    assert result.text == "ok"
    assert client.messages.attempts == 4


async def test_persistent_rate_limit_is_not_turned_into_a_400():
    tools = ScriptedTools({})
    with pytest.raises(anthropic.RateLimitError):
        await run([final()], tools, rate_limit_calls={0, 1, 2, 3, 4})


async def test_cancellation_is_not_swallowed_as_a_tool_error():
    tools = ScriptedTools({"check_stock": {"delay": 5.0}, "shipping_estimate": {"delay": 5.0}})
    task = asyncio.create_task(run([PARALLEL, final()], tools, tool_timeout_s=10))
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
