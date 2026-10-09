# Rubric: fde/w1-c1 Agent loop over the blueprint executor
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Conversation correctness | 15 | Full: assistant content persisted as sent, one user message of tool_result blocks per tool round in tool_use order, is_error from `ToolOutcome.is_error` (held != error), stop on any non-tool_use reason. Partial: correct but fragile (e.g. relies on dict ordering of gather results by completion, string-matching stop reasons loosely). Zero: can produce a 400 from the fake. |
| 3 | Caching layout | 10 | Full: breakpoints only on static system block and last tool, request copies the tools, forced round keeps the tools so the prefix stays warm, and ANSWER.md explains prefix order (tools, system, messages) and why per-request data sits after the breakpoint. Partial: right code, no reasoning. Zero: per-request data before a breakpoint, or tools dropped on the forced round. |
| 4 | Concurrency and robustness | 10 | `asyncio.gather` (or TaskGroup) over tool calls, results zipped back to tool_use order, no shared mutable state across concurrent tools, iteration cap counted on tool rounds, no unbounded loop. |
| 5 | Code quality | 5 | Typed, small functions, no dead code, usage accumulation generic over the four fields. |
| 6 | ANSWER.md trade-offs | 10 | Full: at least two real production concerns with a position: retries/backoff for 429/529, streaming for latency, rolling message breakpoint, per-tool timeouts inside the turn budget, logging usage per call (blueprint `log_model_call`), max_iterations value. Partial: generic. Zero: empty. |
Total: 100
