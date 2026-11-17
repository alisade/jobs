import json

import pytest

from conftest import payload, session
from progress_mcp.catalog_api import CatalogApi

EXPECTED = {"get_learner_progress", "list_lessons", "get_lesson_summary"}


@pytest.mark.asyncio
async def test_exactly_three_read_tools():
    async with session() as (client, _):
        tools = (await client.list_tools()).tools
        assert {t.name for t in tools} == EXPECTED


@pytest.mark.asyncio
async def test_tools_are_annotated_read_only_and_described():
    async with session() as (client, _):
        for t in (await client.list_tools()).tools:
            assert t.annotations is not None and t.annotations.readOnlyHint is True, t.name
            assert t.annotations.destructiveHint in (False, None), t.name
            assert t.description and len(t.description) >= 40, f"{t.name}: write a description the model can choose by"


@pytest.mark.asyncio
async def test_no_tool_takes_a_learner_id():
    async with session() as (client, _):
        for t in (await client.list_tools()).tools:
            props = (t.inputSchema or {}).get("properties", {})
            assert not any("learner" in p.lower() for p in props), f"{t.name} lets the model choose the learner"


@pytest.mark.asyncio
async def test_progress_is_for_the_session_learner_without_answers_or_pii():
    async with session("lrn-ada") as (client, _):
        res = await client.call_tool("get_learner_progress", {"course_id": "bio-210"})
        assert not res.isError
        body = payload(res)
        text = json.dumps(body).lower()
        assert body["mastered"] == ["l4"] and body["in_progress"] == ["l5"]
        assert "memory cells" not in text and "quizanswer" not in text, "never return quiz answers"
        assert "@" not in text, "no email or other PII the tutor does not need"


@pytest.mark.asyncio
async def test_not_enrolled_course_is_an_error():
    async with session("lrn-ada") as (client, _):
        res = await client.call_tool("get_learner_progress", {"course_id": "stats-101"})
        assert res.isError
        assert "enrolled" in res.content[0].text.lower()
        res = await client.call_tool("list_lessons", {"course_id": "stats-101"})
        assert res.isError


@pytest.mark.asyncio
async def test_lesson_summary_scoped_and_bounded():
    async with session("lrn-ada") as (client, _):
        res = await client.call_tool("get_lesson_summary", {"lesson_id": "s1"})
        assert res.isError, "a lesson from a course the learner is not enrolled in"
        res = await client.call_tool("get_lesson_summary", {"lesson_id": "l4"})
        body = payload(res)
        assert len(body["text"]) <= 1500 and body["truncated"] is True
        res = await client.call_tool("get_lesson_summary", {"lesson_id": "nope"})
        assert res.isError


@pytest.mark.asyncio
async def test_lesson_text_is_marked_as_untrusted_data():
    async with session("lrn-ada") as (client, _):
        body = payload(await client.call_tool("get_lesson_summary", {"lesson_id": "l5"}))
        assert body.get("content_trust") == "untrusted", "label course text as data so the agent never treats it as instructions"
        assert "<!--" not in body["text"], "strip HTML comments: hidden text is where injections live"


@pytest.mark.asyncio
async def test_backend_outage_is_an_actionable_error():
    async with session("lrn-ada", CatalogApi(fail=True)) as (client, _):
        res = await client.call_tool("list_lessons", {"course_id": "bio-210"})
        assert res.isError
        msg = res.content[0].text.lower()
        assert "unavailable" in msg and "retry" in msg
        assert "timed out after" not in msg, "do not leak backend internals"


@pytest.mark.asyncio
async def test_no_write_is_reachable():
    api = CatalogApi()
    async with session("lrn-ada", api) as (client, _):
        res = await client.call_tool("record_mastery", {"learner_id": "lrn-ada", "lesson_id": "l5"})
        assert res.isError
    assert api.writes == []
