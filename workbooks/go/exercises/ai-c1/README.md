# go/ai-c1 Secure platform MCP server with the official Go SDK

**Type:** coding | **Estimate:** 2.5 hours | **AI Integration:** 4 Security (also Week 6 Tue, MCP in Go)

## Scenario

Kestrel's triage agent (w6-c1) needs live platform data, so the platform team is
exposing three tools over MCP: `list_deployments`, `get_rollout_status` and the one
mutating tool, `restart_deployment`. Security review blocked the first prototype: it
accepted any bearer token, including tokens the IdP had minted for Grafana; it trusted
a `dry_run` flag the model controlled; and a prompt-injected runbook got the agent to
restart CoreDNS. You are rebuilding it with `github.com/modelcontextprotocol/go-sdk`
over streamable HTTP, with authorization enforced server-side.

## Task

Implement `NewHandler` and `NewServer` in `platformmcp/server.go`. `platform.go`
(in-memory fake platform) and the exported types are given; keep exported names and
signatures. Read the go-sdk `auth` package first: `auth.RequireBearerToken`,
`auth.TokenVerifier`, `auth.TokenInfo` and `auth.ProtectedResourceMetadataHandler` do
much of the HTTP-layer work if you adapt to them correctly.

## Requirements

HTTP layer:

1. `GET /.well-known/oauth-protected-resource` (no auth) serves RFC 9728 metadata:
   `resource` = `Config.ResourceURL`, `authorization_servers`, `scopes_supported`
   (`platform:read`, `platform:write`), `bearer_methods_supported` = `["header"]`.
2. `/mcp` without a bearer token in the `Authorization` header, or with a token the
   `Verifier` rejects (`ErrInvalidToken`), or an expired token: **401** with
   `WWW-Authenticate: Bearer resource_metadata="<Config.MetadataURL>"`. Tokens in the
   query string are never accepted.
3. Audience: reject (401) a token whose audience does not include `Config.ResourceURL`,
   whatever its scopes. No token passthrough.
4. A valid token with neither platform scope: **403**, challenge naming `platform:read`.
   `platform:write` implies `platform:read`.
5. If the verifier fails for any other reason (JWKS endpoint down): **5xx**, not 401.
6. Sessions are bound to the token's subject: another user's valid token replaying a
   session id must be refused (the SDK does this if you give it a user id).

Tools (all with typed inputs via `mcp.AddTool`, and a useful description):

7. `list_deployments {namespace}` and `get_rollout_status {namespace, name}` need
   `platform:read`; `restart_deployment {namespace, name, reason}` needs `platform:write`.
   All three appear in `tools/list` for any authenticated caller; **authorization is
   checked inside each tool call from the verified token**, never from arguments.
8. Namespace and name must be DNS-1123 labels; `reason` is 10-500 characters after
   trimming; restarts in `Config.ProtectedNamespaces` (default `kube-system`,
   `istio-system`) are refused.
9. Restart records the token subject as the audit actor and the trimmed reason.
10. Everything the model can recover from (forbidden, invalid input, protected
    namespace, not found) is a **tool error** (`CallToolResult.IsError`) with an
    actionable message, not a JSON-RPC protocol error. Unknown deployments say so and
    hint at `list_deployments`.
11. `list_deployments` returns structured content `{"deployments": [...]}`, with `[]`
    (not `null`) for an empty namespace.

## Acceptance criteria

- `make test` passes with `-race`; `go vet` is clean.
- Hidden tests drive the server with the go-sdk client and raw HTTP over `httptest`:
  metadata, 401/403/5xx paths and challenges, audience, scopes, write-implies-read,
  restart guards and audit, tool vs protocol errors, structured output, session binding.
- `platform.Restart` is never reached by an unauthorized or invalid call.

## How to run

```
make setup
make test
make run     # optional: local server for MCP Inspector, tokens demo-read / demo-write
```

## What to submit

`platformmcp/server.go` and `ANSWER.md`, then `/grade go/ai-c1` from the workbooks root.

## Study-guide links

- MCP Go SDK: https://github.com/modelcontextprotocol/go-sdk (pkg: https://pkg.go.dev/github.com/modelcontextprotocol/go-sdk/mcp)
- MCP authorization: https://modelcontextprotocol.io/specification/latest/basic/authorization
- MCP security best practices: https://modelcontextprotocol.io/specification/latest/basic/security_best_practices
- OWASP Top 10 for LLM applications: https://genai.owasp.org/llm-top-10/
