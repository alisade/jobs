# Reference: fde/w2-t1 MCP gateway 401s after a JWKS rotation

Injected fault: `gateway.env` sets `JWKS_MIN_REFRESH_INTERVAL=86400` (equal to
`JWKS_CACHE_TTL`). In `gateway/jwks_cache.py`, `KeyCache.get` only refreshes on an unknown
kid when `now - last_fetch >= min_refresh_interval`, so after the startup fetch a rotated-in
kid is rejected for a day ("refresh skipped" is logged at DEBUG only).

Why intermittent: the IdP's staged rollover signs half of new tokens with `k-2026-10`; only
those fail. Existing sessions hold old-kid tokens. Restart fetches both keys and hides it.

Red herring: "token iat is 2s in the future" warnings. The IdP clock is 2 s ahead; leeway
is 30 s; those requests succeed.

Model fix (`.grading/solution/`): interval 30 s, TTL 3600 s, startup validation in
`gateway/config.py` (10 <= interval <= 300, interval < TTL, leeway <= 60). Model
ANSWER.md is in `.grading/solution/ANSWER.md`.

Evidence a strong answer shows: probe split by kid; IdP JWKS has both kids;
`/debug/jwks` has one kid, `fetches: 1`, large `last_fetch_age_s`; the 401 log line with
the kid; the config line and the code branch; live recovery after the cooldown without a
restart.

Better-than-reference ideas: cooldown from the last forced refresh; negative cache for
unknown kids; IdP pre-publishes keys; per-kid 401 alert.

Wrong answers that should lose most root-cause points: NTP/clock skew, "IdP JWKS was
stale", "restart fixed it", raising leeway, removing the rate limit (violates SEC-114).
