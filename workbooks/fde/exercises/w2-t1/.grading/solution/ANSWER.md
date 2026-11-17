# ANSWER: fde/w2-t1 MCP gateway 401s after a JWKS rotation

## Approach

Started from the symptom split: `make probe` gives 50% 401s, and splitting by kid shows
every 401 is on `k-2026-10` and every 200 on `k-2026-09`. So the failure tracks the signing
key, not the customer, the time, or the upstream. The IdP said both keys are published;
checked that, then checked what the gateway actually holds.

```
$ make probe
40 sessions: 20x HTTP 200, 20x HTTP 401
  kid=k-2026-09  HTTP 200: 20
  kid=k-2026-10  HTTP 401: 20
$ curl -s localhost:18210/.well-known/jwks.json | jq -r '.keys[].kid'
k-2026-09
k-2026-10
$ curl -s localhost:18211/debug/jwks
{"kids":["k-2026-09"],"last_fetch_age_s":412.3,"fetches":1}
$ grep 'invalid_token' run/gateway.log | head -2
... WARNING gateway 401 invalid_token kid=k-2026-10 reason=signing key not found
```

One fetch, at startup, and never again despite hundreds of unknown-kid requests. That
points at the refresh-on-miss path in `gateway/jwks_cache.py`.

## Root cause

`KeyCache.get` refreshes on an unknown kid only when
`now - last_fetch >= min_refresh_interval`. `gateway.env` sets
`JWKS_MIN_REFRESH_INTERVAL=86400`, the same value as `JWKS_CACHE_TTL` (copied in
PLAT-2291). The startup fetch happened before the rollover, so for 24 hours every
new-kid token takes the "refresh skipped" branch (logged only at DEBUG) and raises
`KeyNotFound` -> 401. It looks intermittent because the IdP's staged rollover signs only
half of new tokens with the new key, and sessions already in progress hold old-kid tokens.
A restart "fixes" it because the startup fetch then sees both keys.

Red herring: `token iat is 2s in the future (issuer clock ahead?)` is real (the IdP stamps
iat ~2 s ahead) but harmless: leeway is 30 s, and those requests show `POST /mcp 200` on the
next line. Skew never produces "signing key not found".

## Fix

- `gateway.env`: `JWKS_MIN_REFRESH_INTERVAL=30` (SEC-114 asks for at most one forced
  refresh per 10 s; 30 s bounds how long a rotated-in kid can be rejected) and
  `JWKS_CACHE_TTL=3600` (a revoked key ages out within an hour instead of a day).
- `gateway/config.py`: `_validate` refuses to start when the interval is outside 10-300 s
  or not shorter than the TTL, with a message that says why.
- Verification unchanged (RS256 only, aud/iss/exp, 30 s leeway).

Verified: `make test` 8/8 in-process. Live, with the fixed config: `make setup` (gateway
starts, IdP rotates), probe shows 50% 401 for the first 30 s, then with no restart a
second probe shows `40x HTTP 200` and `/debug/jwks` lists both kids with `fetches: 2`.

## Trade-offs / what I would do in production

- Measure the cooldown from the last forced refresh, not from any fetch, so a rotation
  that lands just after a scheduled refresh is not delayed.
- Ask the IdP to publish the next key a day before signing with it; gateways then pick it
  up on a normal refresh and rate limits never matter.
- Alert on 401 rate broken down by kid; a new kid with 100% 401s is this incident.
- Negative-cache unknown kids for the cooldown so junk kids cost no lock round trip.
