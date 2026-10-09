"""Hidden tests for ms/ai-c1: tool design, validation, loop limits, policy enforcement."""
import json
from pathlib import Path

import pytest

from parts_agent.backend import Backend
from parts_agent.fake_model import FakeModelClient, text, tool_use, turn
from parts_agent.loop import run_turn
from parts_agent.session import Session
from parts_agent.tools import TOOLS, execute_tool, validate_input

FIX = Path(__file__).resolve().parents[2] / "fixtures"


def tool(name):
    return next(t for t in TOOLS if t["name"] == name)


def new_session():
    return Session(backend=Backend())


def results_of(message):
    return [(b["tool_use_id"], b["is_error"], json.loads(b["content"])) for b in message["content"]]


def assert_history_valid(messages):
    """Every assistant tool_use is answered, in order, by the next user message."""
    for i, m in enumerate(messages):
        if m["role"] == "assistant" and isinstance(m["content"], list):
            ids = [b["id"] for b in m["content"] if b.get("type") == "tool_use"]
            if ids:
                nxt = messages[i + 1]
                assert nxt["role"] == "user"
                assert [b["tool_use_id"] for b in nxt["content"]] == ids


# ------------------------------------------------------------ tool design


@pytest.mark.parametrize("name", ["search_parts", "get_quote", "place_order"])
def test_tool_definition_quality(name):
    t = tool(name)
    assert 120 <= len(t["description"]) <= 1024, "describe when to use it and what it returns"
    s = t["input_schema"]
    assert s["type"] == "object"
    assert s.get("additionalProperties") is False
    assert s.get("required")
    for prop in s["properties"].values():
        assert prop.get("description"), "every parameter needs a description"


def test_get_quote_schema_constraints():
    s = tool("get_quote")["input_schema"]
    assert set(s["required"]) == {"part_number", "quantity"}
    assert s["properties"]["quantity"]["type"] == "integer"
    assert s["properties"]["quantity"]["minimum"] == 1
    assert s["properties"]["quantity"]["maximum"] == 100
    assert "pattern" in s["properties"]["part_number"]


def test_place_order_takes_only_a_quote_id():
    s = tool("place_order")["input_schema"]
    assert s["required"] == ["quote_id"]
    assert set(s["properties"]) == {"quote_id"}
    assert "confirm" in tool("place_order")["description"].lower()


# ------------------------------------------------------------ validation


def test_validate_input_accepts_valid():
    assert validate_input(tool("get_quote")["input_schema"], {"part_number": "CP-10234", "quantity": 3}) == []


@pytest.mark.parametrize("data,field", [
    ({"part_number": "CP-10234"}, "quantity"),
    ({"part_number": "CP-10234", "quantity": 0}, "quantity"),
    ({"part_number": "CP-10234", "quantity": 101}, "quantity"),
    ({"part_number": "CP-10234", "quantity": "4"}, "quantity"),
    ({"part_number": "CP-10234", "quantity": True}, "quantity"),
    ({"part_number": "CP-10234", "quantity": 2.5}, "quantity"),
    ({"part_number": "10234", "quantity": 4}, "part_number"),
    ({"part_number": "CP-10234", "quantity": 4, "discount": 50}, "discount"),
])
def test_validate_input_rejects(data, field):
    errs = validate_input(tool("get_quote")["input_schema"], data)
    assert errs and any(e.startswith(field) for e in errs), errs


def test_validate_input_non_object():
    assert validate_input(tool("search_parts")["input_schema"], ["seal"])


# ------------------------------------------------------------ execute_tool


def test_unknown_tool_is_structured_error():
    body, is_error = execute_tool(new_session(), "delete_order", {"quote_id": "Q-1"})
    assert is_error and body["error"] == "unknown_tool"
    assert set(body["available"]) == {"search_parts", "get_quote", "place_order"}


def test_invalid_input_is_structured_error():
    body, is_error = execute_tool(new_session(), "get_quote", {"part_number": "CP-10234", "quantity": 500})
    assert is_error and body["error"] == "invalid_input"
    assert any(d.startswith("quantity") for d in body["details"])


def test_backend_errors_become_tool_errors():
    s = new_session()
    body, is_error = execute_tool(s, "get_quote", {"part_number": "CP-99999", "quantity": 1})
    assert is_error and body["error"] == "backend_error"
    body, is_error = execute_tool(s, "get_quote", {"part_number": "CP-30410", "quantity": 50})
    assert is_error and body["error"] == "backend_error" and "stock" in body["message"]


def test_unexpected_exception_does_not_escape(monkeypatch):
    s = new_session()

    def boom(*a, **k):
        raise RuntimeError("db connection reset")

    monkeypatch.setattr(s.backend, "search", boom)
    body, is_error = execute_tool(s, "search_parts", {"query": "seal"})
    assert is_error and body["error"] == "internal_error"


def test_order_requires_quote_from_this_session_and_confirmation():
    a, b = new_session(), Session(backend=None)
    b.backend = a.backend  # same ERP, different conversation
    q, _ = execute_tool(a, "get_quote", {"part_number": "CP-10234", "quantity": 2})
    body, is_error = execute_tool(b, "place_order", {"quote_id": q["quote_id"]})
    assert is_error and body["error"] == "policy_violation"
    body, is_error = execute_tool(a, "place_order", {"quote_id": q["quote_id"]})
    assert is_error and body["error"] == "policy_violation"   # not confirmed yet
    a.confirm(q["quote_id"])
    body, is_error = execute_tool(a, "place_order", {"quote_id": q["quote_id"]})
    assert not is_error and body["status"] == "placed"
    body, is_error = execute_tool(a, "place_order", {"quote_id": q["quote_id"]})
    assert is_error and body["error"] == "policy_violation"   # no double order
    assert len(a.backend.orders) == 1


# ------------------------------------------------------------ loop


def test_injection_is_blocked_server_side():
    fx = json.loads((FIX / "injection.json").read_text())
    client = FakeModelClient(fx["turns"])
    s = new_session()
    res = run_turn(client, s, fx["user_turns"][0])
    assert s.backend.orders == []
    assert res.stop_reason == "end_turn"
    errs = [c["name"] for c in res.tool_calls if c["is_error"]]
    assert errs == ["get_quote", "place_order", "place_order"]
    # the parallel turn: both results in ONE user message, in tool_use order
    parallel = client.requests[2]["messages"][-1]
    ids = results_of(parallel)
    assert [i[0] for i in ids] == ["toolu_12", "toolu_13"]
    assert ids[0][2]["error"] == "invalid_input" and ids[1][2]["error"] == "policy_violation"
    assert_history_valid(s.messages)


def test_parallel_results_keep_model_order():
    script = [
        turn(tool_use("b", "get_quote", {"part_number": "CP-10235", "quantity": 1}),
             tool_use("a", "search_parts", {"query": "valve"}),
             tool_use("c", "nope", {})),
        turn(text("done"), stop="end_turn"),
    ]
    client = FakeModelClient(script)
    s = new_session()
    res = run_turn(client, s, "go")
    msg = client.requests[1]["messages"][-1]
    assert [b["tool_use_id"] for b in msg["content"]] == ["b", "a", "c"]
    assert [b["is_error"] for b in msg["content"]] == [False, False, True]
    assert res.final_text == "done"


def test_max_turns_stops_without_executing_the_last_call():
    script = [turn(tool_use(f"t{i}", "get_quote", {"part_number": "CP-10234", "quantity": 1})) for i in range(10)]
    client = FakeModelClient(script)
    s = new_session()
    res = run_turn(client, s, "loop forever", max_turns=3)
    assert res.stop_reason == "max_turns"
    assert res.model_calls == 3 and len(client.requests) == 3
    assert len(s.backend.quotes) == 2           # third call not executed
    last = s.messages[-1]
    assert last["role"] == "user" and all(b["is_error"] for b in last["content"])
    assert_history_valid(s.messages)
    assert res.final_text


def test_max_tokens_truncated_tool_call_not_executed():
    script = [turn(text("Placing"), tool_use("x", "get_quote", {"part_number": "CP-10234", "quantity": 1}),
                   stop="max_tokens")]
    client = FakeModelClient(script)
    s = new_session()
    res = run_turn(client, s, "quote one")
    assert res.stop_reason == "max_tokens"
    assert s.backend.quotes == {}
    assert_history_valid(s.messages)


def test_model_recovers_from_error_result():
    script = [
        turn(tool_use("1", "get_quote", {"part_number": "CP-10234", "quantity": "two"})),
        turn(tool_use("2", "get_quote", {"part_number": "CP-10234", "quantity": 2})),
        turn(text("Quote Q-1001 ready."), stop="end_turn"),
    ]
    client = FakeModelClient(script)
    s = new_session()
    res = run_turn(client, s, "two seal kits")
    assert [c["is_error"] for c in res.tool_calls] == [True, False]
    assert "Q-1001" in s.quotes


def test_usage_tolerates_missing_fields_and_spans_calls():
    script = [
        {"content": [tool_use("1", "search_parts", {"query": "valve"})], "stop_reason": "tool_use",
         "usage": {"input_tokens": 100}},
        {"content": [text("ok")], "stop_reason": "end_turn"},
    ]
    res = run_turn(FakeModelClient(script), new_session(), "valve?")
    assert res.usage == {"input_tokens": 100, "output_tokens": 0}


def test_history_persists_across_turns():
    script = [turn(text("hi"), stop="end_turn"), turn(text("again"), stop="end_turn")]
    client = FakeModelClient(script)
    s = new_session()
    run_turn(client, s, "one")
    run_turn(client, s, "two")
    roles = [m["role"] for m in client.requests[1]["messages"]]
    assert roles == ["user", "assistant", "user"]
    assert client.requests[1]["system"]
