# ANSWER: healthai/w2-t1 CriteriaService goes dark after a FHIR latency spike

## Approach

Read the metrics lines in the log: `criteria_permits_free` drops 2 -> 1 -> 0 between 09:10 and 09:12 and
stays 0 while FHIR is healthy again. `make repro` shows the same: phase 1 permits 5, phase 2 permits 0,
phase 3 20/20 DEADLINE_EXCEEDED with FHIR fast.

## Root cause

`_check` acquires the semaphore manually and releases it only after a successful FHIR call. The
`except BaseException` branch returns a result on TimeoutError and on CancelledError without releasing,
so every timed-out or cancelled check leaks a permit. After the spike no permits are left; new checks
wait on `acquire()` until the client deadline. CPU is idle because the tasks are parked. Health never
touches the semaphore, so it says SERVING. A restart builds a new semaphore.

## Fix

`async with self.sem:` around the work, `except TimeoutError` and `except Exception` for per-criterion
results, CancelledError allowed to propagate. Repro phase 3 now 20/20 ok with 5 permits free; tests pass.

## Trade-offs / what I would do in production

Export permits-free and queue wait as metrics and alert on them; make readiness reflect capacity; lint
against `except BaseException`; a CI load test with a slow fake FHIR. The FHIR spike was the trigger, not
the cause.
