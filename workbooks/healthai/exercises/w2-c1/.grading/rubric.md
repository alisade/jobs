# Rubric: healthai/w2-c1 CriteriaService on grpc.aio
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Structured concurrency done right | 20 | TaskGroup for the fan-out, `async with` on the semaphore (released on every path), `asyncio.timeout` per check, CancelledError never swallowed (no bare `except:` or `except BaseException`). |
| 3 | gRPC hygiene | 10 | `context.abort` with specific codes, deadline read from `context.time_remaining()`, no blocking calls on the loop, servicer state safe across concurrent RPCs. |
| 4 | ANSWER.md | 15 | Discusses per-instance vs global limits (Cloud Run concurrency x instances vs FHIR quota), deadline propagation from the edge, retries for idempotent reads, streaming results as a design option, HTTP/2 end to end on Cloud Run. |
Total: 100
