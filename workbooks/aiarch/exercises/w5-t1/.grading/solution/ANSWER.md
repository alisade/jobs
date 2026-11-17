# ANSWER: aiarch/w5-t1

## Approach

Compared the exported spans of a parallel turn and a single-tool turn, then read
`lighthouse/agent.py` and reproduced with `make test`.

## Root cause

Since 2.6.0 parallel tool calls run on a `ThreadPoolExecutor` (`POOL.map(_call_tool, ...)`).
OTEL keeps the active span in a `contextvars` context, and executor worker threads do not
inherit the caller's context. In the worker there is no current span, so
`start_as_current_span("execute_tool ...")` starts a new root span in a new trace, and
`propagate.inject` writes that new trace's traceparent to the tool server, which correctly
continues it. Evidence: in `exported-spans-turn-parallel.json` each execute_tool span has
`parentSpanId: null`, its own traceId and a `tool_N` thread, and each tools/call span is a
child of it; in the single-tool turn the call runs on MainThread and everything shares one
trace.

The propagator mismatch is a red herring: both sides speak tracecontext, and the server spans
do have the right parent (the orphaned client span). Sampling cannot create new trace ids.

## Fix

Submit each tool call with `contextvars.copy_context().run`, one copy per task, and collect
results with a timeout. All spans now share the turn's trace, tool calls still overlap.
Verified with make test.

## Trade-offs / what I would do in production

- The same applies to any thread pool, asyncio `run_in_executor` and background tasks; wrap the
  executor once (or use the OTEL threading instrumentation) rather than at each call site.
- Keep parent-based sampling on the tool server so it follows the agent's decision.
- Add a trace-shape test to CI: one root per turn, every tool span under it.
