# Rubric: fde/ai-t1 Intermittent 400s from the Messages API after a "latency win" release
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: names the exact mechanism: exceptions from `asyncio.gather(return_exceptions=True)` (raised or timed-out tools) are skipped, so a `tool_use` id goes unanswered and the API rejects the next request with 400 `invalid_request_error`. Partial (10): "missing tool_result" without why it is missing, or blames gather/parallelism itself. Zero: rate limits, SDK bump, or the API. |
| 3 | Evidence | 20 | Full: quotes the Sentry message (message index + missing id), shows the failing request (assistant with N tool_use, user with fewer tool_result), and correlates `tool_calls` vs `tools_done` counts in the logs; notes the failure was logged at DEBUG and so invisible. Partial: one source only. Zero: assertion without evidence. |
| 4 | Red herring handled | 10 | Full: explains with evidence why the 429s are unrelated (retried successfully; the failed turn with a 429 fails on a later request; they are newly logged, not newly occurring). Partial: dismisses them without evidence. Zero: proposes a rate-limit increase or removes the retry. |
| 5 | Fix quality | 10 | Full: one `tool_result` per `tool_use` in order, `is_error: true` with sanitized text (no raw exception message), cancellation re-raised, parallelism kept, failure logged at WARNING with tool name. Partial: correct but leaks exception text or serializes the tools. Zero: catches and drops in a different place. |
| 6 | Production trade-offs | 5 | Names a guard that would have caught it (strict API fake / invariant test, alert on 400 vs 5xx, calls != results metric) and takes a position on rollback vs fix-forward. |
Total: 100
