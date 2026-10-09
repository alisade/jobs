# fde/w2-c1 - JWT/JWKS-authenticated streamable-HTTP MCP server

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 2 (Mon: MCP servers, Tue: MCP authorization, Wed: JWT / JWKS verification)

## Scenario

Northwind Outfitters is moving its shopping agent to Managed Agents. The hosted agent
reaches the storefront tools over MCP (streamable HTTP), so the MCP server is now on the
network and the blueprint is explicit about what that means: "The reference MCP servers
bind to loopback unless an environment variable states that an authenticating gateway is in
front of them" (`docs/safety.md`, MCP binding) and "a production server derives the
customer from the authenticated request" (`storefront-mcp-server/README.md`, Identity).

Northwind's IdP (`https://login.northwind.example/`) issues RS256 and ES256 access tokens
for the resource `https://mcp.northwind.example/mcp`, with a `scope` claim (`cart:read`,
`cart:write`). Keys rotate monthly; the next rotation is in two weeks and the IdP team wants
proof the MCP server survives it without a restart. Security review has three findings
from the last vendor's server you must not repeat: it accepted `alg: none`, it verified an
HS256 token using the RSA public key as the HMAC secret, and anyone could mint random `kid`
values to make it hammer the JWKS endpoint.

`mcp_auth/app.py` (given) is a FastMCP server over the blueprint's `ShoppingToolExecutor`
and the retail `MockRetail` backend. It builds one session per verified principal from
`request.state.principal`; it never takes a user id as a tool argument.

## What you build

Edit three files (the TODOs). `settings.py` and `app.py` are given.

1. `mcp_auth/jwks.py` - `JWKSCache.get_key(kid)`: fetch on first use and after `ttl_s`;
   refresh on an unknown kid (that is how a rotation arrives) but at most one unknown-kid
   refresh per `refresh_cooldown_s`; single-flight under concurrency; keep serving the last
   good set when a refresh fails.
2. `mcp_auth/verifier.py` - `TokenVerifier.verify(token) -> Principal`: alg pinned to
   `settings.algorithms` and to the key's type, signature, `iss`, `aud` (the resource),
   `exp`/`nbf` with `leeway_s`, every claim in `required_claims`, scopes from `scope`.
3. `mcp_auth/middleware.py` - `protected_resource_metadata` (RFC 9728) and
   `BearerAuthMiddleware` (pure ASGI).

## Acceptance criteria

- No or non-Bearer credentials: `401` with
  `WWW-Authenticate: Bearer resource_metadata="https://mcp.northwind.example/.well-known/oauth-protected-resource/mcp"`.
- Bad token: `401` with `error="invalid_token"`; the reason is logged, never returned.
- `alg: none`, HS256-with-the-public-key, algorithms outside the allow-list, and an alg that
  does not match the key type are all rejected. RS256 and ES256 both work.
- Wrong `aud` or `iss`, missing `exp`/`sub`/`iat`, `nbf` in the future: rejected. A token
  that expired 10 s ago is accepted (30 s leeway).
- A new kid published by the IdP verifies without a restart; the old kid keeps working
  during the overlap; 25 random unknown kids cause at most one extra JWKS fetch; a key the
  IdP removed stops working after `cache_ttl_s`; a JWKS outage keeps the last good keys,
  and a cold-start outage is a `401`, not a `500`; 12 concurrent cold verifications share
  one fetch.
- `tools/call` of `add_to_cart` (single message or inside a JSON-RPC batch) without
  `cart:write`: `403` with `error="insufficient_scope", scope="cart:write"`. Read tools work
  with `cart:read`.
- `/.well-known/oauth-protected-resource` and `/.well-known/oauth-protected-resource/mcp`
  are public and return `resource`, `authorization_servers`, `scopes_supported`,
  `bearer_methods_supported`.
- Two principals get separate carts and separate provenance.

## How to run

```bash
make setup     # builds/reuses the shared venv fde/.venv (blueprint installed editable)
make test      # visible tests: happy path, 401 challenge, metadata, expired token
# from workbooks/: /grade fde/w2-c1    (adds hidden tests for every criterion above)
make clean
```

The tests need no network: `tests/w2c1_support.py` runs an in-memory IdP (real RSA/EC keys,
JWKS served through `httpx.MockTransport`) and drives the app in-process with
`httpx.ASGITransport`, including a real MCP client session over streamable HTTP.

Read first: the MCP Authorization spec (resource server section), RFC 9728 sec. 2-3 and 5.1,
RFC 8725 sec. 2 (the attacks list), PyJWT's `PyJWK` and `jwt.decode` options.

## What to submit

Your three files and a filled-in `ANSWER.md`. Explain your cooldown rule (what an attacker
can and cannot make the server do) and why the scope check lives in the middleware rather
than in the tool.
