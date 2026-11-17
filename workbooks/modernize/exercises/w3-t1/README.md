# modernize/w3-t1 - 401s for some adjusters after the IdP rotated its signing key

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 3 (Wed: token pitfalls: issuer, audience, clock skew, key rotation)

## Symptom

ClaimDesk's API now accepts Okta access tokens (the gateway module in this folder). Since
Tuesday morning about 40% of adjusters get "Session expired, please sign in again" on claim
pages. Signing in again does not reliably help; refreshing a few times usually does. Nothing
was deployed since Friday. On-call suspects clock drift on one node. Read `evidence/PAGE.txt` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/` | the page, gateway access log (4 nodes), gateway startup log, the Okta system log, the JWKS as served now, an NTP log |
| `src/main/java/.../TokenVerifier.java` | verifies tokens at the API edge |
| `src/main/java/.../JwksCache.java` | the identity provider's signing keys, by `kid` |
| `src/test/java/.../FakeIdp.java` | a local IdP with rotating keys, a JWKS endpoint that counts fetches, and a controllable clock |

## Your task

1. Find the root cause and prove it with the logs: which requests fail, on which nodes, since
   when, and why some users and some retries succeed. Rule the clock-drift theory in or out.
2. Fix `JwksCache` without putting the JWKS endpoint on every request: refresh after `maxAge`,
   refresh on an unknown `kid` at most once per `minRefreshInterval` (an attacker can send random
   kids), keep the cached keys if a refresh fails, and let concurrent misses share one refresh.
   Keep the constructor and `key(kid)` signatures.
3. Write `ANSWER.md`: Approach, Root cause (commands and output excerpts), Fix (and how you
   verified it), Trade-offs / production follow-ups.

## Acceptance criteria (what the grader checks)

- Tokens signed with a newly rotated key verify on a long-running node; tokens signed with the
  previous key still verify while it is published.
- An unknown kid causes at most one fetch per refresh interval, also under concurrency; known
  kids cause none.
- After `maxAge` the cache drops keys the IdP no longer publishes; an IdP outage does not wipe keys.
- `ANSWER.md` names the mechanism with evidence; "clock skew" or "restart fixed it" does not pass.

## How to run

```bash
make setup      # JDK 21 + Maven, downloads artifacts once
make test       # visible tests (one fails until you fix the cache)
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade modernize/w3-t1
make clean
```

Useful: `awk '{print $2, $5, $8}' evidence/access.log | sort | uniq -c`.
