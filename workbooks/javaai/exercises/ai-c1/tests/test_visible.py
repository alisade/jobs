import pytest

from conftest import payload, session


@pytest.mark.asyncio
async def test_server_lists_tools():
    async with session() as (client, _):
        tools = (await client.list_tools()).tools
        assert tools, "the server exposes tools"


@pytest.mark.asyncio
async def test_lessons_for_an_enrolled_course():
    async with session() as (client, _):
        names = [t.name for t in (await client.list_tools()).tools]
        name = "list_lessons" if "list_lessons" in names else "get_lessons"
        res = await client.call_tool(name, {"course_id": "bio-210"})
        assert not res.isError
