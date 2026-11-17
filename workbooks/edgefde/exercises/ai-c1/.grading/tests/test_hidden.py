"""Hidden eval suite for edgefde/ai-c1: 15 recorded scenarios."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from conftest import call, final, tool_turn  # noqa: E402

from assistant import agent, data, router, tools  # noqa: E402
from assistant.llm import StubLLM  # noqa: E402

Q = "Why did machine 4 alert at 14:05?"


def tool_msgs(llm, n):
    return [m for m in llm.calls[n]["messages"] if m.get("role") == "tool"]


def test_parallel_tool_calls_both_returned():
    llm = StubLLM("local", [tool_turn(call("c1", "get_alerts", machine="P04"),
                                      call("c2", "get_feature_history", machine="P04", start="2026-11-12T13:00:00Z", end="2026-11-12T15:00:00Z")),
                            final(citations=("c1", "c2"))])
    res = agent.run(llm, Q)
    assert res.status == "ok"
    msgs = tool_msgs(llm, 1)
    assert [m["tool_call_id"] for m in msgs] == ["c1", "c2"]
    assert len(json.loads(msgs[1]["content"])["windows"]) == 3


def test_retry_once_with_validation_error_fed_back():
    llm = StubLLM("local", [tool_turn(call("c1", "get_alerts", machine="P04")), final(raw="Machine 4 alerted."), final()])
    res = agent.run(llm, Q)
    assert res.status == "ok" and res.retries == 1
    last_user = [m for m in llm.calls[2]["messages"] if m["role"] == "user"][-1]["content"]
    assert "valid" in last_user.lower() or "json" in last_user.lower()


def test_two_invalid_replies_give_invalid():
    llm = StubLLM("local", [tool_turn(call("c1", "get_alerts", machine="P04")), final(raw="nope"), final(raw="{}")])
    res = agent.run(llm, Q)
    assert res.status == "invalid" and res.answer is None


def test_citation_must_be_an_executed_call():
    llm = StubLLM("local", [tool_turn(call("c1", "get_alerts", machine="P04")), final(citations=("c9",)), final(citations=("c9",))])
    assert agent.run(llm, Q).status == "invalid"


def test_action_outside_enum_rejected():
    llm = StubLLM("local", [tool_turn(call("c1", "get_alerts", machine="P04")), final(action="set_threshold"), final(action="disable_alarm")])
    assert agent.run(llm, Q).status == "invalid"


def test_confidence_bounds():
    llm = StubLLM("local", [tool_turn(call("c1", "get_alerts", machine="P04")), final(confidence=1.7), final(confidence=0.4)])
    res = agent.run(llm, Q)
    assert res.status == "ok" and res.answer.confidence == 0.4


def test_unknown_tool_is_a_recoverable_error():
    llm = StubLLM("local", [tool_turn(call("c1", "set_alert_threshold", machine="P04", db=30)),
                            tool_turn(call("c2", "get_alerts", machine="P04")), final(citations=("c2",))])
    res = agent.run(llm, Q)
    assert res.status == "ok"
    err = json.loads(tool_msgs(llm, 1)[0]["content"])
    assert "error" in err


def test_bad_arguments_return_error_not_exception():
    llm = StubLLM("local", [tool_turn(call("c1", "get_alerts", machine="P99"), call("c2", "get_feature_history", machine="P04")),
                            tool_turn(call("c3", "get_alerts", machine="P04")), final(citations=("c3",))])
    res = agent.run(llm, Q)
    assert res.status == "ok"
    errs = [json.loads(m["content"]) for m in tool_msgs(llm, 1)]
    assert all("error" in e for e in errs)


def test_max_turns_stops_the_loop():
    llm = StubLLM("local", [tool_turn(call(f"c{i}", "get_model_card")) for i in range(20)])
    res = agent.run(llm, Q, max_turns=4)
    assert res.status == "max_turns" and len(llm.calls) == 4


def test_tools_do_not_mutate_data():
    before = json.dumps([data.ALERTS, data.FEATURES, data.MODEL_CARD], sort_keys=True)
    out = tools.get_alerts("P04")
    out["alerts"].clear()
    tools.get_model_card()["version"] = "hacked"
    assert json.dumps([data.ALERTS, data.FEATURES, data.MODEL_CARD], sort_keys=True) == before


def test_since_filter():
    assert [a["id"] for a in tools.get_alerts("P04", since="2026-11-12T15:00:00Z")["alerts"]] == ["A-1043"]


def test_fallback_to_cloud_when_allowed():
    local = StubLLM("local", [tool_turn(call("c1", "get_raw_capture", machine="P04")), final(raw="x"), final(raw="y")], latency_ms=900)
    cloud = StubLLM("cloud", [tool_turn(call("k1", "get_alerts", machine="P04")), final(citations=("k1",))], latency_ms=1500)
    res = router.answer(Q, local, cloud, router.Policy(allow_cloud=True))
    assert res.status == "ok" and res.model == "cloud"
    assert res.latency_ms == 900 * 3 + 1500 * 2


def test_no_fallback_when_policy_forbids():
    local = StubLLM("local", [final(raw="x"), final(raw="y")])
    cloud = StubLLM("cloud", [final()])
    res = router.answer(Q, local, cloud, router.Policy(allow_cloud=False))
    assert res.status == "invalid" and res.model == "local" and not cloud.calls


def test_cloud_never_sees_raw_waveforms():
    local = StubLLM("local", [tool_turn(call("c1", "get_raw_capture", machine="P04")), final(raw="x"), final(raw="y")])
    cloud = StubLLM("cloud", [tool_turn(call("k1", "get_raw_capture", machine="P04")), tool_turn(call("k2", "get_alerts", machine="P04")), final(citations=("k2",))])
    router.answer(Q, local, cloud, router.Policy(allow_cloud=True))
    blob = json.dumps(cloud.calls)
    assert "samples" not in blob
    for c in cloud.calls:
        assert "get_raw_capture" not in [t["name"] for t in c["tools"]]


def test_complex_question_goes_straight_to_cloud_when_allowed():
    q = "Compare the trend on P04 with P07 and explain why one alert was closed."
    local = StubLLM("local", [])
    cloud = StubLLM("cloud", [tool_turn(call("k1", "get_alerts", machine="P04")), final(citations=("k1",))])
    res = router.answer(q, local, cloud, router.Policy(allow_cloud=True, cloud_for_complex=True))
    assert res.model == "cloud" and res.status == "ok" and not local.calls
