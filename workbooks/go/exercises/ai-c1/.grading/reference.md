# Reference: go/ai-c1 secure platform MCP server

Reference code: `.grading/solution/platformmcp/server.go`.

## Layering

```
GET /.well-known/oauth-protected-resource   auth.ProtectedResourceMetadataHandler (public)
/mcp  ->  auth.RequireBearerToken(adapter, {ResourceMetadataURL, Scopes: [platform:read]})
      ->  mcp.NewStreamableHTTPHandler(server)
      ->  tool handler: scope check from req.Extra.TokenInfo, validation, guards, platform call
```

## The SDK helpers, and why to use them

go-sdk v1.8.0 ships `auth.RequireBearerToken`. It extracts the header token, calls a
`TokenVerifier`, maps errors (`auth.ErrInvalidToken` -> 401, `auth.ErrOAuth` -> 400,
anything else -> 500), enforces required scopes (403) and expiry (401), writes the
`WWW-Authenticate: Bearer resource_metadata="...", scope="..."` challenge, and puts
`*auth.TokenInfo` in the request context under a private key. The streamable transport
reads that key to (a) expose `req.Extra.TokenInfo` to tool handlers and (b) bind each
session to `TokenInfo.UserID`, refusing a different user on the same `Mcp-Session-Id`
with 403. A hand-written middleware cannot set that private key, so it loses both: this
is the main trap in the exercise.

## The adapter is where the policy lives

- Map the app's `ErrInvalidToken` to `auth.ErrInvalidToken` (401); leave other errors
  unwrapped so an IdP outage returns 500 instead of telling every client to re-auth.
- Audience must contain the canonical resource URI: tokens minted for other services
  are rejected (the MCP spec forbids token passthrough; this is the confused-deputy fix).
- Normalise `platform:write` to also grant `platform:read` once, here.
- Set `UserID` to the subject.

## Tools

- `mcp.AddTool` with typed inputs infers the JSON schema and validates arguments
  before the handler runs (missing `name` never reaches the platform).
- Returning a Go error from a typed handler becomes an `IsError` result: the model sees
  "forbidden: restart_deployment requires scope platform:write" and can tell the user,
  rather than the session failing with a JSON-RPC error.
- Scope checks inside each tool are the real enforcement. The HTTP-layer scope only
  gates entry. Listing all tools and enforcing at call time keeps `tools/list` stable
  (better for prompt caching) and gives the model an explainable denial; filtering the
  list per token is also defensible, but you still must check at call time.
- Protected namespaces and the reason requirement are server-side policy that no prompt
  injection can talk its way past.

## Production notes a strong answer mentions

- Verifier: JWKS fetched and cached with rotation, `iss`/`aud`/`exp`/`nbf` checks,
  small clock skew (`RequireBearerTokenOptions.ClockSkew`).
- Downstream calls use the server's own identity (Pod Identity / a k8s SA with scoped
  RBAC) or OAuth token exchange, never the caller's token.
- Mutating tools: human confirmation (elicitation) or a change ticket; per-subject rate
  limits; audit to a durable sink, not only logs.
- Defence in depth on EKS: Istio `RequestAuthentication` + `AuthorizationPolicy` on the
  MCP server, NetworkPolicy, and OTel spans per tool call with the subject.
