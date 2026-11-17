# ANSWER: connect/w7-c1 ServiceNow incident Lambda

## Approach

<!-- What you changed first and why; how you used the fake's fault injection to prove each behavior. -->

## Fix

<!-- Token cache, 401/429 handling and the budget, pagination, idempotency, error contract.
How you verified it (tests, numbers). -->

## Trade-offs / what I would do in production

<!-- Short. E.g. where the client secret lives, idempotency beyond correlation_id (race between two
concurrent invokes), async invoke vs sync, moving creation to an after-contact event, ServiceNow
rate-limit rules, observability. -->
