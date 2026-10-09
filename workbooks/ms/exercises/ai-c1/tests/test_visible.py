"""Visible tests: the happy path. Hidden tests cover failure paths, limits and the injection."""
import json

from parts_agent.tools import TOOLS


def test_tool_names():
    assert [t["name"] for t in TOOLS] == ["search_parts", "get_quote", "place_order"]


def test_happy_path_places_one_order(replay_fixture):
    client, session, results = replay_fixture("happy_path.json")
    first, second = results
    assert first.stop_reason == "end_turn" and "Q-1001" in first.final_text
    assert [c["name"] for c in first.tool_calls] == ["search_parts", "get_quote"]
    assert second.stop_reason == "end_turn"
    assert [o["order_id"] for o in session.backend.orders] == ["O-5001"]


def test_tool_results_go_back_to_the_model(replay_fixture):
    client, session, _ = replay_fixture("happy_path.json")
    # request 2 must carry the result of the search_parts call from request 1
    last = client.requests[1]["messages"][-1]
    assert last["role"] == "user"
    block = last["content"][0]
    assert block["type"] == "tool_result" and block["tool_use_id"] == "toolu_01"
    assert block["is_error"] is False
    body = json.loads(block["content"])
    assert body["results"][0]["part_number"] == "CP-10234"
    assert client.requests[0]["tools"] == TOOLS


def test_usage_is_summed(replay_fixture):
    _, _, results = replay_fixture("happy_path.json")
    assert results[0].usage == {"input_tokens": 812 + 1240 + 1410, "output_tokens": 52 + 38 + 61}
    assert results[0].model_calls == 3
