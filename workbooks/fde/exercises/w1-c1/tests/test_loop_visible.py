"""Visible tests: the happy path and the request layout. Hidden tests cover the rest of
the README's acceptance criteria."""

from __future__ import annotations

from w1c1_support import STATIC, TOOLS, dynamic

from agent_loop import build_request, run_turn


def test_request_layout_puts_breakpoints_after_static_system_and_last_tool():
    req = build_request(
        model="claude-sonnet-5",
        static_system=STATIC,
        dynamic_context=dynamic(),
        tools=TOOLS,
        messages=[{"role": "user", "content": "hi"}],
    )
    assert req["system"][0] == {"type": "text", "text": STATIC, "cache_control": {"type": "ephemeral"}}
    assert req["system"][1]["text"] == dynamic() and "cache_control" not in req["system"][1]
    assert req["tools"][-1]["cache_control"] == {"type": "ephemeral"}
    assert "tool_choice" not in req


async def test_parallel_tools_then_end_turn(make_rig):
    rig = make_rig("yoga_mat_parallel")
    result = await run_turn(rig.client, rig.executor, **rig.kwargs(user_text="a yoga mat and headphones, add the mat"))
    assert result.stop_reason == "end_turn"
    assert result.rounds == 3
    assert result.final_text.startswith("Added the ACME Fit 6mm mat")
    # user, assistant, tool results, assistant, tool results, assistant
    assert [m["role"] for m in result.messages] == ["user", "assistant", "user", "assistant", "user", "assistant"]
    cart = await rig.backend.get_cart(rig.session)
    assert [(i.product_id, i.quantity) for i in cart.items] == [("AR-1301", 1)]
