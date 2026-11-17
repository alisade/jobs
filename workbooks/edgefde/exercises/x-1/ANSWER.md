# ANSWER: edgefde/x-1 CMMS work-order client

## Approach

<!-- How you structured the retry loop, auth and pagination; how you tested with the fake clock. -->

## Fix

<!-- What you implemented. Why the idempotency key (and where it comes from) prevents duplicates,
and why retries alone make duplicates more likely. -->

## Trade-offs / what I would do in production

<!-- httpx with timeouts and connection pools, tenacity vs hand-written, secrets from a vault, a
circuit breaker or an outbox when the CMMS is down for hours, metrics on retries. Short. -->
