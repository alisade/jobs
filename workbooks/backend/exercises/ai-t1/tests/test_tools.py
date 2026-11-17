from assistant_tools.replay import replay
from assistant_tools.tools import call_tool
from testkit import leaked


def test_find_account_in_own_tenant(amer):
    r = call_tool(amer, "find_account", {"query": "cobalt"})
    assert not r["is_error"]
    assert [a["id"] for a in r["content"]["accounts"]] == ["acc-amer-0002"]


def test_replaying_inc_7731_leaks_nothing():
    results = replay("transcripts/inc-7731.json")
    assert leaked(results, "bu-amer") == []
