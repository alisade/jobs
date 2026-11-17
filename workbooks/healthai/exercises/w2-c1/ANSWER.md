# ANSWER: healthai/w2-c1 CriteriaService on grpc.aio

## Approach

<!-- How the servicer is structured: validation, TaskGroup, semaphore, per-check budget. -->

## Fix

<!-- What you changed from the draft and how the tests prove bounded concurrency and clean cancellation. -->

## Trade-offs / what I would do in production

<!-- Per-instance vs global concurrency limits (Cloud Run concurrency, FHIR store quotas), retries and
idempotency for FHIR reads, deadline propagation from the edge, health checks on Cloud Run with HTTP/2,
when you would choose server streaming here. -->
