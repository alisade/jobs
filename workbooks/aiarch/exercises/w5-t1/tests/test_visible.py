from util import CALLS, by_name, run


def test_single_tool_call_is_one_trace():
    _, spans = run(CALLS[:1])
    assert len({s.context.trace_id for s in spans}) == 1


def test_parallel_tool_calls_stay_in_the_agent_trace():
    out, spans = run(CALLS)
    assert [o.get("state") for o in out] == ["scheduled", "open", None]
    assert len({s.context.trace_id for s in spans}) == 1, "tool spans started new traces"
