# Reference: fde/w2-c1 JWT/JWKS-authenticated MCP server

Full code: `.grading/solution/mcp_auth/{jwks,verifier,middleware}.py`.

## Verifier order

1. `jwt.get_unverified_header` (malformed -> InvalidToken).
2. `alg` must be in `settings.algorithms` (rejects `none`, HS256, RS384 here).
3. `kid` -> `JWKSCache.get_key(kid)`; `UnknownKid` / `JWKSUnavailable` -> InvalidToken
   (a cold JWKS outage is a 401, not a 500).
4. `alg` must match the key type (`RS*` -> RSA, `ES*` -> EC). This closes the HS/RS
   confusion even if someone later adds HS256 to the allow-list for an internal issuer.
5. `jwt.decode(token, key.key, algorithms=[alg], audience=resource, issuer=issuer,
   leeway=30, options={"require": ["iss","aud","sub","exp","iat"]})`.

## JWKS cache

- TTL refresh (forced) when `now - fetched_at >= ttl`.
- Unknown kid: one refresh, then at most one unknown-kid refresh per cooldown window.
  The cooldown is tracked separately from the TTL fetch, so a rotation that lands right
  after a scheduled fetch is still picked up immediately. An attacker minting random kids
  gets one JWKS fetch per 30 s, total, regardless of request rate.
- Single flight: read `fetched_at` before the lock, re-check after acquiring; whoever
  waited reuses the result.
- Outage: keep the last good set (and push `fetched_at` so we do not refetch every call);
  with no keys at all raise `JWKSUnavailable`.

## Middleware

- Pure ASGI so it can buffer the body for `tools/call` inspection and replay it with a
  wrapped `receive` (BaseHTTPMiddleware makes body replay awkward and breaks streaming).
- 401 challenge: `Bearer resource_metadata="..."`; with a token present also
  `error="invalid_token"`. 403: `error="insufficient_scope", scope="cart:write"`.
- The principal goes into `scope["state"]["principal"]`; FastMCP hands the tool the
  Starlette `Request` for that POST (`ctx.request_context.request.state.principal`).

## Why scope in the middleware

The tool cannot return HTTP 403; it can only return a tool error, which the model reads and
may retry or paper over. The 403 with `insufficient_scope` is what an OAuth client (the
Managed Agents platform) acts on to step up. The tool still never trusts arguments for
identity.

## Production notes worth hearing

- Negative-cache unknown kids for the cooldown to avoid even the lock round trip.
- Prefer per-session sender-constrained tokens (DPoP or mTLS) for the platform hop.
- Revocation: local JWT verification cannot see revocation before `exp`; keep `exp` short
  (5-15 min) or add introspection for high-risk tools (checkout).
- Log `sub` as a digest; the token itself never.
