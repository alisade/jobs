# Reference: edgefde/x-1

The reference client is `.grading/solution/cmms/client.py`.

- Key: `"wo-" + sha256(machine|window)[:32]`. Deterministic from the anomaly, so a retry, a restarted
  gateway or a second gateway reporting the same anomaly all send the same key and the CMMS returns
  the existing order. A UUID per call would defeat it.
- One `_send` loop for every request: transport timeout always set; 401 -> one forced token refresh
  without consuming an attempt; 2xx/3xx return; non-retryable 4xx -> `PermanentError`; retryable ->
  wait = Retry-After (seconds or HTTP date via `parsedate_to_datetime`) or full jitter
  `uniform(0, min(cap, base * 2**attempt))`; if total sleep would exceed the budget, raise before
  sleeping; give up after `max_attempts`.
- Token cached with its expiry and refreshed 30 s early.
- Pagination follows `next_page_token` with a hard page limit.

Retries make duplicates MORE likely without a key: every commit-then-timeout becomes a second order.
In production: httpx with connect/read timeouts and a pool, secrets from the plant vault, an outbox
table on the gateway so an hours-long CMMS outage queues orders instead of exhausting the budget,
and metrics for attempts, waits and permanent errors.
