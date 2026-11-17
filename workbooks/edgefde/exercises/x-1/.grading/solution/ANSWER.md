# ANSWER: edgefde/x-1 CMMS work-order client

## Approach

Wrote one `_send` loop that every call goes through (token, create, list), then drove it with
scripted faults on the fake clock: each fault kind alone, then 30% random faults over 40 anomalies.

## Fix

The duplicate problem is not solved by retries; retries make it worse. When the CMMS commits the
order and the response is lost, the client cannot tell that from a failed request, so it must retry,
and without a key that retry is a second order. The key is derived from the anomaly (machine and
alert window), so every retry, a restarted gateway and a second gateway reporting the same anomaly
send the same key and get the same order back. The loop retries only 429/5xx/timeouts with full
jitter, uses Retry-After when given (seconds or HTTP date), checks the budget before sleeping, and
refreshes the token once on a 401 without counting it as an attempt.

## Trade-offs / what I would do in production

httpx with explicit connect/read timeouts and a pool; the client secret from the plant vault; an
outbox table on the gateway so a CMMS outage of hours queues orders rather than failing them; metrics
for attempts, waits and permanent errors, and an alert when permanent errors appear (they mean a
contract change, not a flaky link).
