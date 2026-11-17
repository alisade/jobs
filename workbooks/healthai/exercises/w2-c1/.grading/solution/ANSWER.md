# ANSWER: healthai/w2-c1 CriteriaService on grpc.aio

## Approach

Validate first with `context.abort` (INVALID_ARGUMENT, NOT_FOUND). Then one TaskGroup task per
criterion; each task takes the semaphore with `async with` and runs FHIR under `asyncio.timeout(budget)`,
where budget is the smaller of the configured timeout and the client's remaining time minus a margin.

## Fix

Timeouts and dependency errors are results, so one slow search cannot fail the case. CancelledError is
never caught, so a client cancel or deadline cancels the RPC task, the TaskGroup cancels the children, and
the semaphore is released by the context manager. Tests show peak in-flight 5, no leftover work after a
cancel, and a following request still gets 5-way concurrency.

## Trade-offs / what I would do in production

The limit is per instance: real FHIR load is limit x Cloud Run concurrency x instances, so set it from the
Healthcare API quota. Propagate the edge deadline into every gRPC call. Retry idempotent reads once within
budget. Stream results if reviewers want progressive display. Cloud Run needs HTTP/2 end to end for gRPC.
