from conftest import call, final, tool_turn

from assistant import agent, router, tools
from assistant.llm import StubLLM


def test_tools_return_data():
    assert [a["id"] for a in tools.get_alerts("P04")["alerts"]] == ["A-1042", "A-1043"]
    assert tools.get_model_card()["version"] == "v7"


def test_happy_path_cites_tool_call():
    llm = StubLLM("local", [tool_turn(call("c1", "get_alerts", machine="P04")), final()])
    res = agent.run(llm, "Why did machine 4 alert at 14:05?")
    assert res.status == "ok"
    assert res.answer.citations == ["c1"]
    assert res.turns == 2


def test_router_stays_local_by_default():
    local = StubLLM("local", [tool_turn(call("c1", "get_model_card")), final()])
    cloud = StubLLM("cloud", [])
    res = router.answer("Which model version is deployed?", local, cloud, router.Policy())
    assert res.status == "ok" and res.model == "local" and not cloud.calls
