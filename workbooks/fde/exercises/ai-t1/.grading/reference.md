# Reference: fde/ai-t1 Intermittent 400s

Injected fault: `agentloop/loop.py` skips every gather outcome that is an exception
(raised tool, per-tool `asyncio.wait_for` timeout, unknown tool), so the next request
carries a `tool_use` id with no `tool_result` and the Messages API answers 400
`invalid_request_error`: "messages.4: `tool_use` ids were found without `tool_result`
blocks immediately after: <id>". Four of 140 recorded turns hit it (3 `InventoryTimeout`,
1 timeout in turn-0098). The failure was logged at DEBUG, so the INFO bundle only shows
`tool_calls` with two tools followed by `tools_done results=1`.

Red herring: 429s on 6 turns, retried successfully by the new retry code; the only failed
turn with a 429 (turn-0024) fails on a later request with the 400.

Fixed loop: `.grading/solution/agentloop/loop.py`. The essential part:

```python
outcomes = await asyncio.gather(
    *(asyncio.wait_for(toolbox.call(c.name, dict(c.input)), tool_timeout_s) for c in calls),
    return_exceptions=True,
)
tool_results = []
for call, outcome in zip(calls, outcomes, strict=True):      # gather keeps call order
    if isinstance(outcome, asyncio.CancelledError):
        raise outcome
    if isinstance(outcome, BaseException):
        _event("tool_failed", logging.WARNING, tool=call.name, error=type(outcome).__name__, ...)
        tool_results.append({"type": "tool_result", "tool_use_id": call.id, "is_error": True,
                             "content": f"{call.name} is temporarily unavailable "
                                        f"({type(outcome).__name__}). Continue with what you have ..."})
    else:
        tool_results.append({"type": "tool_result", "tool_use_id": call.id, "content": outcome})
messages.append({"role": "user", "content": tool_results})
```

Model answer: `.grading/solution/ANSWER.md`.

Points an interviewer probes:
- The API contract: tool_result blocks lead the next user message, one per tool_use id;
  any text goes after them. Order is not required by the API but keeping `tool_use` order
  makes logs and replays diffable.
- `is_error: true` is how the model learns a tool failed and recovers (says what it could
  not check, or tries another tool); "skip and the model will ask again" breaks the
  protocol.
- `return_exceptions=True` also captures `CancelledError` of children; re-raise it.
- Why the bug was invisible: the failure path logged at DEBUG while the new 429 retries
  logged at WARNING, which pulled attention to the wrong signal.
- Prevention: a strict fake API in tests, an invariant check before every request, and
  separate alerting for 400s (always a client bug) vs 429/5xx.
