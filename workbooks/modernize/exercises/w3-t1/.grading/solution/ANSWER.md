# ANSWER: modernize/w3-t1 401s after the IdP rotated its signing key

## Approach

Counted the access log by node, status and kid before touching the clock theory:
`awk '{print $2, $5, $8}' evidence/access.log | sort | uniq -c`.

## Root cause

Every 401 has kid=k-2026-11 and is on cdk-app-01, 02 or 04 (9, 6, 6); cdk-app-03 serves k-2026-11 with
200 (6). The Okta system log shows `system.signing_key.rotate` to k-2026-11 at 2026-11-10T14:00Z, with the
old key still published. startup.log: 01/02/04 started on 2026-11-09 and loaded `1 key(s) [k-2026-10]`;
03 rebooted on 2026-11-11 and loaded both. JwksCache parses the JWKS once in the constructor and never
refreshes, so long-running nodes cannot verify tokens signed after the rotation. Users who signed in before
Tuesday hold old-kid tokens and are fine; retries work when the load balancer picks cdk-app-03.

Not NTP: 18 s is inside the 60 s skew, and cdk-app-01 and 04 fail the same way with good clocks.

## Fix

JwksCache refreshes after maxAge, refreshes on an unknown kid at most once per minRefreshInterval with one
shared refresh for concurrent misses, and keeps the cached keys when a refresh fails. Verified with the
FakeIdp tests (rotation, flood, outage, retirement, concurrency).

## Trade-offs / what I would do in production

Now: rolling restart of 01, 02, 04 (safe now that the cause is known), then ship the fix. Add metrics for
JWKS refreshes and 401s by reason and kid, alert on a 401 spike for one kid. Rehearse key rotation in the
Okta preview tenant before each release. maxAge 1 h and a 30 s refresh interval keep the IdP off the hot
path while bounding staleness.
