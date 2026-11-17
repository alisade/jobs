# Reference: healthai/w2-t1

Root cause in `criteria/server.py` `_check`: `await self.sem.acquire()` then `self.sem.release()` only
after a successful FHIR call. The `except BaseException` branch (added for INC-47702 so one criterion
cannot fail the batch) returns a `timeout`/`error` result without releasing, and catches CancelledError
too. During the spike every check timed out, so 5 permits leaked within seconds; the metrics line shows
`criteria_permits_free=0` from 09:12 until the restart. Later requests park on `acquire()` (no CPU) until
the edge's 1 s deadline. Health does not use the semaphore, so Cloud Run saw a healthy revision. A
redeploy creates a new semaphore.

Fix: `async with self.sem:` around the call, `except TimeoutError` -> timeout result, `except Exception`
-> error result, `finally` for the inflight gauge; never catch CancelledError. The repro then shows phase
3 fully recovered with 5 permits free.
