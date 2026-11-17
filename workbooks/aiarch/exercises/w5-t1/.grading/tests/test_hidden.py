import time
from pathlib import Path

from opentelemetry.trace import SpanKind

from util import CALLS, by_name, run


def _root(spans):
    return [s for s in spans if s.parent is None]


def test_exactly_one_root_span():
    _, spans = run(CALLS)
    roots = _root(spans)
    assert [r.name for r in roots] == ["invoke_agent change_assistant"]


def test_execute_tool_spans_are_children_of_invoke_agent():
    _, spans = run(CALLS)
    root = by_name(spans, "invoke_agent")[0]
    tools = by_name(spans, "execute_tool")
    assert len(tools) == 3
    assert all(t.parent.span_id == root.context.span_id for t in tools)


def test_server_spans_are_children_of_their_execute_tool_span():
    _, spans = run(CALLS)
    clients = {s.context.span_id: s for s in by_name(spans, "execute_tool")}
    servers = by_name(spans, "tools/call")
    assert len(servers) == 3
    for s in servers:
        assert s.kind == SpanKind.SERVER
        assert s.parent is not None and s.parent.span_id in clients


def test_genai_attributes_present():
    _, spans = run(CALLS)
    for t in by_name(spans, "execute_tool"):
        assert t.attributes["gen_ai.operation.name"] == "execute_tool"
        assert t.attributes["gen_ai.tool.name"] == "get_change"
        assert t.kind == SpanKind.CLIENT


def test_tools_still_run_in_parallel():
    t0 = time.perf_counter()
    run(CALLS * 2)
    assert time.perf_counter() - t0 < 0.045, "six 10 ms tool calls should overlap"


def test_two_turns_are_two_traces():
    _, a = run(CALLS)
    _, b = run(CALLS)
    assert {s.context.trace_id for s in a}.isdisjoint({s.context.trace_id for s in b})


def test_answer_names_thread_context():
    t = Path("ANSWER.md").read_text().lower()
    assert "thread" in t and "context" in t
