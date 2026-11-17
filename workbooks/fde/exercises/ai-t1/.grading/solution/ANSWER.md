# ANSWER: fde/ai-t1 Intermittent 400s from the Messages API

## Approach

Started from the Sentry issue rather than the 429 theory: a 400 is the API rejecting the
request shape, a rate limit is a 429, so they are different failures. Grouped Sentry
events, read the failing request body, then lined up the breadcrumbs of each failed turn
against the loop code.

```
$ jq -r '.exception.value' run/sentry/events.jsonl | cut -c1-200 | sort | uniq -c
   4 Error code: 400 - {... 'messages.4: `tool_use` ids were found without `tool_result`
     blocks immediately after: toolu_01.... Each `tool_use` block must have a
     corresponding `tool_result` block in the next message.'}}
$ cat run/metrics.txt   ->  140 turns, 4 http_400_turns (2.9%), 6 turns_with_429_retry
```

## Root cause

Release 2.14.0 runs a round's tool calls with `asyncio.gather(..., return_exceptions=True)`
and then, per the changelog item "a tool that fails or times out is skipped",
`loop.py` drops every outcome that is an exception (`if isinstance(outcome,
BaseException): ... continue`). The assistant message still contains that tool's
`tool_use` block, so the next request has a `tool_use` id with no `tool_result`, and the
Messages API rejects the whole request with 400 `invalid_request_error`. The turn dies on
the request after the failure, which is why the user sees an error mid-chat.

Evidence:

- `run/failing_request.json`: `messages[3]` (assistant) has two `tool_use` blocks
  (`check_stock`, `shipping_estimate`); `messages[4]` (user) has a single `tool_result`, for
  `shipping_estimate`. The 400 names exactly the missing `check_stock` id.
- Breadcrumbs of every failed turn: `tool_calls tools=["check_stock","shipping_estimate"]`
  followed by `tools_done results=1`. On healthy turns the counts match.
  `jq -c 'select(.event=="tools_done")' run/logs/agent.jsonl` vs `tool_calls` shows the
  mismatch only on the four failed turn_ids.
- The failure itself was logged at DEBUG (`log.debug("tool %s failed")`), so it never
  reached the INFO log: the inventory errors (3 `InventoryTimeout`, 1 per-tool timeout in
  turn-0098) were invisible, which is why the logs looked clean apart from the 429s.
- ~3% matches the rate at which inventory-svc times out on a parallel round.

The 429s are a red herring: they appear on 6 turns, 5 of which succeed; the retry code
works (the 429 is retried and the next attempt is accepted). The one failed turn that
also had a 429 (turn-0024) failed on a later request, with the 400 above. The 429s are
also not new load: before 2.14.0 they were not retried, so they were not logged.

## Fix

In `agentloop/loop.py` every outcome of the gather becomes exactly one `tool_result`, in
`tool_use` order (gather preserves argument order; `zip(..., strict=True)` guards it):
- success -> `{"type": "tool_result", "tool_use_id": id, "content": output}`
- exception or per-tool timeout -> `is_error: true` with a short text naming the tool and
  the exception class only ("check_stock is temporarily unavailable (InventoryTimeout).
  Continue with what you have..."). Raw exception text is not sent: it carries internal
  hostnames and pool names.
- `CancelledError` is re-raised, not reported as a tool failure.
- Tool failures are logged at WARNING (`tool_failed`, tool name, id, error class), and
  `tools_done` now logs `calls`, `results`, `failed`.
An unknown tool name goes through the same path (the toolbox raises), so it is answered too.

Verification: `make replay` -> `140 turns: 0 failed with HTTP 400`, error rate 0.0%, and
the four previously failing turns end with the recorded "could not check stock" answer.
`make test` passes. Parallelism unchanged (still one gather per round).

## Trade-offs / what I would do in production

- Invariant test in CI: for any assistant message with N `tool_use` blocks, the next user
  message starts with N matching `tool_result` blocks. A strict fake of the API (as here)
  catches this class of bug before deploy; mocks that accept anything do not.
- Alert on `tools_done.calls != tools_done.results` and on 400 `invalid_request_error`
  separately from 5xx/429: a 400 is always our bug.
- Fix forward rather than roll back: the defect is four lines and rollback loses the
  latency win; ship behind the canary that would have caught it.
- Never "skip" a failed tool: the model needs an `is_error` result to recover (say what it
  could not check, retry later, or pick another tool).
- Request a rate-limit increase only after the 429 rate is measured independently of
  retries; the retries were working as designed.
