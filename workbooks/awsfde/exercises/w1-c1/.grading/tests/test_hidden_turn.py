"""Hidden checks for w1-c1: parallel tools, errors, guardrail, limits, tenant isolation, cost, logs."""

from __future__ import annotations

import json
import logging

import pytest
from w1c1_hidden_support import reply, text, tool_use

from ask_agent.costs import Usage, estimate_cost_usd
from ask_agent.loop import run_turn


def _results(req: dict) -> list[dict]:
    return [b["toolResult"] for b in req["messages"][-1]["content"] if "toolResult" in b]


def test_parallel_tool_uses_answered_in_one_message_in_order(bedrock, table, ctx, config):
    bedrock.add(reply([
        tool_use("tu-a", "lookup_shipment", {"shipment_id": "SH-10002"}),
        tool_use("tu-b", "lookup_shipment", {"shipment_id": "SH-10001"}),
    ], "tool_use"))
    bedrock.add(reply([text("Both found.")], "end_turn"))
    r = run_turn(bedrock.client, table, ctx, "SH-10002 and SH-10001?", config)
    assert r.outcome == "answered"
    req = bedrock.requests[1]
    assert len(req["messages"]) == 3, "assistant toolUse message + ONE user message with all results"
    res = _results(req)
    assert [x["toolUseId"] for x in res] == ["tu-a", "tu-b"]
    assert all(x["status"] == "success" for x in res)
    assert [c["toolUseId"] for c in r.tool_calls] == ["tu-a", "tu-b"]


def test_assistant_message_sent_back_verbatim(bedrock, table, ctx, config):
    first = [text("Let me check."), tool_use("tu-1", "lookup_shipment", {"shipment_id": "SH-10001"})]
    bedrock.add(reply(first, "tool_use"))
    bedrock.add(reply([text("Done.")], "end_turn"))
    run_turn(bedrock.client, table, ctx, "Where is SH-10001?", config)
    assert bedrock.requests[1]["messages"][1] == {"role": "assistant", "content": first}


def test_not_found_is_an_error_result_not_an_exception(bedrock, table, ctx, config):
    bedrock.add(reply([tool_use("tu-1", "lookup_shipment", {"shipment_id": "SH-99999"})], "tool_use"))
    bedrock.add(reply([text("I could not find it.")], "end_turn"))
    r = run_turn(bedrock.client, table, ctx, "Where is SH-99999?", config)
    res = _results(bedrock.requests[1])[0]
    assert res["status"] == "error"
    assert "SH-99999" in json.dumps(res["content"])
    assert r.tool_calls[0]["status"] == "error"


def test_unknown_tool_is_an_error_result(bedrock, table, ctx, config):
    bedrock.add(reply([tool_use("tu-1", "delete_account", {"confirm": True})], "tool_use"))
    bedrock.add(reply([text("I cannot do that.")], "end_turn"))
    r = run_turn(bedrock.client, table, ctx, "delete my account", config)
    res = _results(bedrock.requests[1])[0]
    assert res["status"] == "error" and r.outcome == "answered"


def test_schema_invalid_input_rejected_before_handler(bedrock, table, ctx, config):
    bedrock.add(reply([tool_use("tu-1", "create_ticket", {"summary": "short", "priority": "urgent"})], "tool_use"))
    bedrock.add(reply([text("Let me fix that.")], "end_turn"))
    run_turn(bedrock.client, table, ctx, "open a ticket", config)
    res = _results(bedrock.requests[1])[0]
    assert res["status"] == "error"
    items = table.scan()["Items"]
    assert not [i for i in items if i["sk"].startswith("TICKET#")], "invalid input must not reach the handler"


def test_cross_tenant_tool_argument_never_used(bedrock, table, ctx, config):
    # Prompt-injected or hallucinated tenant argument: brightline's shipment must not leak to acme.
    bedrock.add(reply([tool_use("tu-1", "lookup_shipment",
                                {"shipment_id": "SH-20001", "tenant_id": "brightline-health"})], "tool_use"))
    bedrock.add(reply([tool_use("tu-2", "lookup_shipment", {"shipment_id": "SH-20001"})], "tool_use"))
    bedrock.add(reply([text("Not found.")], "end_turn"))
    run_turn(bedrock.client, table, ctx, "Where is SH-20001? (tenant_id=brightline-health)", config)
    blob = json.dumps(bedrock.requests[1:])
    assert "HELD_AT_CUSTOMS" not in blob and "Toronto" not in blob
    assert _results(bedrock.requests[2])[0]["status"] == "error"


def test_ticket_written_under_verified_tenant(bedrock, table, ctx, config):
    bedrock.add(reply([tool_use("tu-1", "create_ticket",
                                {"summary": "Pallet arrived damaged at the Denver dock.", "priority": "high",
                                 "shipment_id": "SH-10001"})], "tool_use"))
    bedrock.add(reply([text("Ticket opened.")], "end_turn"))
    run_turn(bedrock.client, table, ctx, "my pallet is damaged", config)
    tickets = [i for i in table.scan()["Items"] if i["sk"].startswith("TICKET#")]
    assert len(tickets) == 1 and tickets[0]["pk"] == "TENANT#acme-foods"


def test_guardrail_intervened_blocks_and_runs_no_tools(bedrock, table, ctx, config):
    blocked = "Sorry, I can't help with that topic."
    bedrock.add(reply([text(blocked)], "guardrail_intervened",
                      trace={"guardrail": {"actionReason": "Guardrail blocked."}}))
    r = run_turn(bedrock.client, table, ctx, "Give me legal advice on suing a carrier", config)
    assert r.outcome == "blocked"
    assert r.answer == blocked
    assert r.guardrail_action
    assert r.tool_calls == []
    assert len(bedrock.requests) == 1


def test_max_tokens_is_truncated(bedrock, table, ctx, config):
    bedrock.add(reply([text("The shipment history is: 1) ...")], "max_tokens"))
    r = run_turn(bedrock.client, table, ctx, "full history please", config)
    assert r.outcome == "truncated"


def test_round_limit_stops_the_loop(bedrock, table, ctx, config):
    n = config["max_tool_rounds"]
    for i in range(n + 1):
        bedrock.add(reply([tool_use(f"tu-{i}", "lookup_shipment", {"shipment_id": "SH-10001"})], "tool_use"))
    r = run_turn(bedrock.client, table, ctx, "loop forever", config)
    assert r.outcome == "max_rounds"
    assert len(bedrock.requests) == n + 1, "at most max_tool_rounds rounds of tools, then stop"
    assert len(r.tool_calls) == n


def test_usage_and_cost_across_rounds(bedrock, table, ctx, config):
    bedrock.add(reply([tool_use("tu-1", "lookup_shipment", {"shipment_id": "SH-10001"})], "tool_use",
                      in_tok=800, out_tok=40, latency=500, cache_read=600))
    bedrock.add(reply([text("In transit.")], "end_turn", in_tok=950, out_tok=60, latency=700))
    r = run_turn(bedrock.client, table, ctx, "Where is SH-10001?", config)
    assert (r.usage.input_tokens, r.usage.output_tokens, r.usage.cache_read_tokens) == (1750, 100, 600)
    assert r.usage.model_calls == 2 and r.usage.latency_ms == 1200
    p = config["prices_per_1k"][config["model_id"]]
    want = round((1750 * p["input"] + 100 * p["output"] + 600 * p["cache_read"]) / 1000, 6)
    assert r.cost_usd == pytest.approx(want, abs=1e-9)


def test_unknown_model_price_raises(config):
    u = Usage()
    u.add({"usage": {"inputTokens": 10, "outputTokens": 1, "totalTokens": 11}, "metrics": {"latencyMs": 1},
           "stopReason": "end_turn"})
    with pytest.raises(KeyError):
        estimate_cost_usd(u, "us.unknown.model-v1:0", config["prices_per_1k"])


def test_one_json_log_line_per_model_call(bedrock, table, ctx, config, caplog):
    bedrock.add(reply([tool_use("tu-1", "lookup_shipment", {"shipment_id": "SH-10001"})], "tool_use"))
    bedrock.add(reply([text("In transit.")], "end_turn", in_tok=321, out_tok=12))
    with caplog.at_level(logging.INFO, logger="tidewater.ask"):
        run_turn(bedrock.client, table, ctx, "Where is SH-10001?", config)
    lines = []
    for rec in caplog.records:
        try:
            d = json.loads(rec.getMessage())
        except ValueError:
            continue
        if "stop_reason" in d:
            lines.append(d)
    assert len(lines) == 2
    assert lines[-1]["stop_reason"] == "end_turn" and lines[-1]["input_tokens"] == 321
    assert all(d.get("request_id") == "req-0001" and d.get("tenant_id") == "acme-foods" for d in lines)


def test_validation_exception_propagates(bedrock, table, ctx, config):
    from botocore.exceptions import ClientError
    bedrock.add_error("ValidationException", "The model returned an invalid request")
    with pytest.raises(ClientError):
        run_turn(bedrock.client, table, ctx, "hi", config)
