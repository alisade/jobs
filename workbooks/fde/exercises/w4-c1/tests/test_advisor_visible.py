"""Visible tests: one happy path per tool. The grader adds hidden tests for the edge cases,
redaction, input validation and error results."""

from __future__ import annotations

from w4c1_support import GOOD_POLICY, call

TOOLS = {"list_reason_codes", "explain_decision", "validate_policy_config", "list_hooks_covered", "decision_stats"}


async def test_all_tools_are_listed_read_only_with_output_schemas(advisor):
    async with advisor() as session:
        tools = {t.name: t for t in (await session.list_tools()).tools}
    assert set(tools) == TOOLS
    for tool in tools.values():
        assert tool.annotations is not None and tool.annotations.readOnlyHint is True, tool.name
        assert tool.outputSchema is not None, f"{tool.name} has no structured output"
        assert tool.description and len(tool.description) > 40, tool.name


async def test_explain_decision_happy_path(advisor):
    async with advisor() as session:
        is_error, data, _ = await call(session, "explain_decision", {"decision_id": "hx-1006-000106"})
    assert not is_error
    assert data["outcome"] == "deny" and data["hook"] == "checkout"
    assert [e["code"] for e in data["explanations"]] == ["velocity_high"]
    assert len(data["session_digest"]) == 16


async def test_validate_policy_config_accepts_the_reference_policy(advisor):
    async with advisor() as session:
        is_error, data, _ = await call(session, "validate_policy_config", {"yaml_text": GOOD_POLICY})
    assert not is_error
    assert data["valid"] is True and data["findings"] == []


async def test_list_hooks_covered_on_a_well_wired_backend(advisor):
    async with advisor() as session:
        is_error, data, _ = await call(
            session, "list_hooks_covered", {"backend": "trust_advisor.sample_backends:GoodTrusted"}
        )
    assert not is_error
    assert data["ok"] is True and data["missing"] == []
    covered = {h["hook"]: h["covered"] for h in data["hooks"]}
    assert covered == {
        "add_to_cart": True, "update_cart_item": True, "remove_from_cart": False, "checkout_handoff": True,
    }


async def test_decision_stats_over_everything(advisor):
    async with advisor() as session:
        is_error, data, _ = await call(session, "decision_stats", {"last_n": 1000})
    assert not is_error
    assert data["window"] == 60 and sum(data["counts"].values()) == 60
