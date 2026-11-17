# Rubric: modernize/w3-t1 401s after the IdP rotated its signing key
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (5 tests already pass on the starter: 2 visible and 3 hidden guards against fixes that fetch on every request or wipe keys) |
| 2 | Root cause identified | 25 | Full: JwksCache loads the JWKS once at startup and never refreshes; Okta rotated the signing key on 2026-11-10 14:00 UTC (09:00 ET) and signs new tokens with k-2026-11; nodes started before that (01, 02, 04) only know k-2026-10, so tokens issued after the rotation fail there; cdk-app-03 rebooted on Wednesday and knows both keys, which is why round-robin retries sometimes work and why users who signed in before Tuesday (old-kid tokens) are fine. Partial (10-15): "key rotation" without the startup-only cache or the node pattern. Zero: clock skew. |
| 3 | Evidence | 20 | Full: per-node counts showing every 401 is kid=k-2026-11 on 01/02/04 and none on 03; startup log key lists; the Okta rotate/activate events; the JWKS now holding both keys. Partial: one or two. |
| 4 | Red herring handled | 10 | Rules out NTP: 18 s is inside the 60 s skew, cdk-app-01 and 04 fail identically with a correct clock, and failures follow the kid, not the node clock. |
| 5 | Fix and production | 15 | Full: refresh on unknown kid with a rate limit, maxAge refresh, keep keys on failure, single-flight under concurrency; immediate mitigation (rolling restart of 01/02/04, which is safe now that the cause is known); metrics (JWKS refresh count, 401 by reason and kid) and an alert; rehearse rotation in preview with Okta's manual rotation. Partial: "restart the nodes". |
Total: 100
