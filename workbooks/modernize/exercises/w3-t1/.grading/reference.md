# Reference: modernize/w3-t1

Cause: `JwksCache` parses the JWKS once in its constructor (CLM-4521 kept the endpoint off the request path)
and ignores maxAge and minRefreshInterval. Okta rotated keys at 2026-11-10T14:00Z; new tokens carry kid
k-2026-11. Nodes 01/02/04 started on 2026-11-09 with only k-2026-10; node 03 rebooted on 2026-11-11 and has
both. The access log shows every 401 is kid=k-2026-11 on 01/02/04 and node 03 never fails. Old sessions
(tokens issued before the rotation) keep working until they expire; new sign-ins fail on 3 of 4 nodes,
and round-robin retries land on node 03 a quarter of the time.

NTP: 18 s drift is within the 60 s skew, and the failures follow the kid, not the clock.

Fix: `.grading/solution/src/main/java/com/corvane/claimdesk/gateway/JwksCache.java`: refresh after maxAge,
refresh on unknown kid at most once per minRefreshInterval (single-flight via synchronized + identity check),
keep keys on fetch failure. Mitigation now: rolling restart of 01, 02, 04. Prevention: metrics on refreshes
and 401 reasons by kid, and a rotation rehearsal in the preview tenant.
