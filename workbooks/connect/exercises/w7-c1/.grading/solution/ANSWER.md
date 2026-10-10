# ANSWER: connect/w7-c1 ServiceNow incident Lambda

## Approach

Read the fake's fault knobs first and wrote one failing test per pilot symptom (token per call,
first page only, throw on 429, duplicates), then fixed the client before the orchestration.

## Fix

Module-scope token cache with a 60 s skew, refresh once on 401; one 6.5 s deadline threaded through
every call; 429 honors Retry-After only if it fits, max 3 retries; pagination follows Link rel=next;
lookup-before-create on correlation_id=ContactId across all pages; every failure returns
status=DEGRADED as a flat string map. Verified with the full suite and the fault-injection cases.

## Trade-offs / what I would do in production

Concurrent invokes can still both create: add a DynamoDB conditional put on ContactId before the
POST. Client secret from Secrets Manager. Consider creating the incident from an EventBridge
contact event after the call if the IVR does not need the number. Metric + alarm on DEGRADED.
