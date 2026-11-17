"""Visible checks for w1-c1 (the happy paths). The grader runs more."""

from __future__ import annotations

from w1c1_support import reply, text, tool_use

from ask_agent.loop import build_request, run_turn


def test_request_has_model_tools_guardrail(config):
    req = build_request(config, [{"role": "user", "content": [{"text": "hi"}]}])
    assert req["modelId"] == config["model_id"]
    names = [t["toolSpec"]["name"] for t in req["toolConfig"]["tools"]]
    assert names == ["lookup_shipment", "create_ticket"]
    assert req["guardrailConfig"]["guardrailIdentifier"] == "gr-tw-ask-prod"
    assert req["guardrailConfig"]["trace"] == "enabled"
    assert req["inferenceConfig"]["maxTokens"] == 1024


def test_plain_answer(bedrock, table, ctx, config):
    bedrock.add(reply([text("Hello! Ask me about a shipment.")], "end_turn"))
    r = run_turn(bedrock.client, table, ctx, "hi", config)
    assert r.outcome == "answered"
    assert r.answer == "Hello! Ask me about a shipment."
    assert r.usage.model_calls == 1


def test_one_tool_round(bedrock, table, ctx, config):
    bedrock.add(reply([text("Checking."), tool_use("tu-1", "lookup_shipment", {"shipment_id": "SH-10001"})], "tool_use"))
    bedrock.add(reply([text("SH-10001 is in transit to Denver, ETA 2026-11-16.")], "end_turn"))
    r = run_turn(bedrock.client, table, ctx, "Where is SH-10001?", config)
    assert r.outcome == "answered"
    second = bedrock.requests[1]["messages"]
    assert second[1]["role"] == "assistant"
    result = second[2]["content"][0]["toolResult"]
    assert result["toolUseId"] == "tu-1" and result["status"] == "success"
    assert result["content"][0]["json"]["status"] == "IN_TRANSIT"


def test_cost_is_positive(bedrock, table, ctx, config):
    bedrock.add(reply([text("ok")], "end_turn", in_tok=1000, out_tok=100))
    r = run_turn(bedrock.client, table, ctx, "hi", config)
    assert r.cost_usd == round((1000 * 0.003 + 100 * 0.015) / 1000, 6)
