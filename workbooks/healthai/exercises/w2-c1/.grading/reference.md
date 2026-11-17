# Reference: healthai/w2-c1

See `.grading/solution/criteria/server.py`.
- `_check` wraps the whole FHIR call in `async with self.sem`, so the slot is released on success,
  timeout, error and cancellation alike. `except Exception` (not BaseException) keeps CancelledError
  propagating, which is what lets the TaskGroup and grpc.aio tear the work down.
- `asyncio.timeout` inside the semaphore measures FHIR latency, not queueing. If you put it outside, a
  queued check can time out without ever calling FHIR; say which one you chose and why.
- The TaskGroup only raises if a child raises; turning timeouts and dependency errors into results keeps
  one slow lab search from failing the whole case.
- Deadline: `context.time_remaining()` is None without a client deadline. Shrinking the budget lets the
  server answer `timeout` instead of the client seeing DEADLINE_EXCEEDED with no partial results.
- Production: the semaphore is per instance; with Cloud Run concurrency 80 and N instances the FHIR store
  sees up to 5 x 80 x N calls. Pair it with a quota-aware limiter or Healthcare API quota alarms.
