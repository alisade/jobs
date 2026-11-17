# go/ai-t1 The copilot lost its cluster tools after the Istio upgrade

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **AI Integration:** 4 Security (auth in front of MCP servers), 7 Observability

## Scenario

Kestrel Bank's support copilot (`agents/agent-runtime`) reaches cluster data through an MCP
server, `mcp-tools/k8s-tools` (streamable HTTP on `:8080/mcp`). Zero-trust is enforced in
the mesh: an Istio `AuthorizationPolicy` lets only the `agent-runtime` identity call the
MCP endpoint, and the MCP server also validates a projected service-account JWT.

Since about 06:40 UTC every MCP call returns `403 RBAC: access denied`, so the copilot
answers without tools. Nobody deployed either app. The mesh team ran an Istio 1.25 -> 1.27
canary upgrade last night and reported it clean. EKS also announced an OIDC signing-key
rotation this week, and one engineer suspects the JWT.

Start with `artifacts/PAGER.md`.

## What you have

- `artifacts/`: pager, upgrade change record, `kubectl`/`istioctl` output, the installed
  sidecar-injector webhook (`artifacts/istio/`), an Envoy RBAC/JWT config dump, the MCP
  server sidecar's access log and RBAC debug log, agent-runtime logs.
- `manifests/`: the desired state ArgoCD applies (namespaces, both workloads, the
  AuthorizationPolicies, PeerAuthentications, RequestAuthentication).
- `meshsim/`: an offline model of injection + mTLS + AuthorizationPolicy evaluation that
  reads `manifests/` and `artifacts/istio/`. `make test` replays the failing call through
  it. Do not edit the model or the webhook artifact; they stand in for the live cluster.

## Task

1. Find the root cause and explain the full chain from the upgrade to the 403, including
   why it started at 06:40 and not at 19:10 the evening before.
2. Fix `manifests/` with the smallest change that follows the platform standard (ADR-017:
   namespaces opt in with `istio.io/rev=<revision>`; no `default` revision tag).
3. Harden the MCP server so that a caller without a sidecar can never again arrive as an
   anonymous plaintext peer: `mcp-tools` must require mTLS (`STRICT`). Do not change the
   mesh-wide default; `batch` is deliberately outside the mesh.
4. Fill in `ANSWER.md`, including what you would run on the live cluster to apply and
   verify the fix.

## Constraints

- Do not weaken authorization: the ALLOW policy keeps exactly the `agent-runtime`
  principal, methods and paths; the admin DENY policy stays; no mesh-wide policies.
- Leave the `RequestAuthentication` alone unless the evidence says it is the problem.

## Acceptance criteria

- `make test` passes: agent-runtime gets 200 on POST/GET/DELETE `/mcp` over mTLS.
- Hidden tests confirm the namespace follows ADR-017, authorization is not weakened, other
  identities are still denied, the admin path is still denied and unmeshed callers are
  rejected at the transport layer.
- `ANSWER.md` names the root cause with quoted evidence and rules out the JWT theory.

## How to run

```
make setup   # builds the model, prints the page
make test    # visible tests + call matrix (make check prints just the matrix)
make clean
```

No cluster is needed.

## What to submit

Your edits under `manifests/` and `ANSWER.md`, then `/grade go/ai-t1`.

## Study-guide links

- Istio AuthorizationPolicy reference: https://istio.io/latest/docs/reference/config/security/authorization-policy/
- Istio security concepts (peer auth, identity): https://istio.io/latest/docs/concepts/security/
- MCP authorization: https://modelcontextprotocol.io/specification/latest/basic/authorization
- MCP security best practices: https://modelcontextprotocol.io/specification/latest/basic/security_best_practices
