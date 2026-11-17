# Rubric: healthai/w2-t1 CriteriaService goes dark after a FHIR latency spike
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause and evidence | 40 | Full: `_check` acquires the semaphore manually and releases it only on the success path; the `except BaseException` handler returns a result on timeout and cancellation without releasing, and also swallows CancelledError. Each timed-out or cancelled check leaks a permit; after the spike `criteria_permits_free=0` (log 09:12-09:35, repro phase 2-3), so every later request waits on `acquire()` until the client deadline. Explains idle CPU (tasks parked on the semaphore), SERVING health (Health never touches the semaphore), restart (new process, new semaphore). Partial: leak found without the mechanism or evidence. Zero: blames FHIR latency or timeouts. |
| 3 | Fix quality | 15 | `async with self.sem` (or try/finally) around the work, `except TimeoutError` and `except Exception` instead of BaseException, CancelledError propagates, per-criterion results preserved. |
| 4 | Red herring and prevention | 15 | FHIR spike identified as trigger, not cause. Prevention: alert on permits free / queue wait, health or readiness reflecting capacity, lint rule against `except BaseException`, chaos/load test with a slow dependency in CI. |
Total: 100
