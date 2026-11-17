from testkit import call, session, token

EXPECTED = {"find_account", "get_account_timeline", "log_activity", "propose_lead_assignment"}


async def test_tools_are_listed(world):
    async with session(world, token()) as c:
        tools = {t.name for t in (await c.list_tools()).tools}
    assert tools == EXPECTED


async def test_find_account_sees_only_own_business_unit(world):
    async with session(world, token()) as c:
        err, data = await call(c, "find_account", {"query": "cobalt"})
    assert not err
    assert [a["id"] for a in data["accounts"]] == ["acc-amer-002"]


async def test_timeline_of_own_account(world):
    async with session(world, token()) as c:
        err, data = await call(c, "get_account_timeline", {"account_id": "acc-amer-001", "limit": 2})
    assert not err and len(data["items"]) == 2
