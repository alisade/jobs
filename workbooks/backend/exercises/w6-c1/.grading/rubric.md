# Rubric: backend/w6-c1 Lead assignment workflow with manager approval
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Durable-execution correctness | 15 | Full: all side effects in activities, timers via wait_condition timeout or workflow.sleep (no asyncio.sleep on wall time, no datetime.now, no random), state kept in workflow fields, status query reflects every stage. Partial: works but mixes logic that would break on replay (e.g. reads env vars or time in workflow code). |
| 3 | Approval semantics | 15 | Full: approve is an update with a validator that checks the region manager and rejects duplicate/late decisions without mutating state; reject is a signal; owner override supported; ANSWER explains why the validator runs before history (rejected updates leave no trace) and why a signal cannot return an error. Partial: checks inside the handler (accepted then ignored). |
| 4 | Idempotency and retries | 10 | Key from workflow id (plus a step name), never uuid4 or time; retry policy with sensible intervals and ValidationError non-retryable; timeouts on every activity. |
| 5 | ANSWER.md | 10 | Versioning plan for in-flight executions (patched / worker versioning), how the primitive is exposed (API, typed input, search attributes), and an agent angle (agents start it, never approve it). Concrete, with positions. |
Total: 100
