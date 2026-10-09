# Reference: go/ai-t1 The copilot lost its cluster tools after the Istio upgrade

## Root cause

The `agents` namespace was missed in the canary relabel (CHG-7781 step 2) and still has
`istio-injection=enabled`. That label was served by the 1.25 default-revision injector
(`istio-sidecar-injector`), which step 3 uninstalled. ADR-017 means there is no `default`
revision tag, so nothing answers for `istio-injection=enabled` anymore. The only injector
left, `istio-sidecar-injector-1-27-1`, has two webhooks and **both** require
`istio-injection DoesNotExist` on the namespace, so the label actively blocks revision
injection too.

Chain: Karpenter consolidation at 06:40 recreated the agent pods -> no webhook matched ->
pods start with only the `agent` container (READY 1/1, absent from proxy-status) -> the
client sends plaintext HTTP -> k8s-tools' sidecar accepts it because PeerAuthentication is
PERMISSIVE -> the connection has no peer certificate, so no principal -> the ALLOW policy
requires principal `cluster.local/ns/agents/sa/agent-runtime` -> nothing matches ->
`403 RBAC: access denied`, `rbac_access_denied_matched_policy[none]`.

Why not at 19:10: the old pods still had 1.25 sidecars with cached xDS config and a
workload certificate valid for up to 24 h. Removing istiod does not remove running
sidecars, so mTLS kept working (22:31 log line, 200, SNI `outbound_.8080_...`) until the
pods were replaced.

Evidence: `kubectl-get-ns.txt` (agents: injection enabled, no rev), `kubectl-get-pods.txt`
(1/1 vs 2/2), describe (no istio-init/istio-proxy, compare to the 2026-10-03 events),
`istioctl-proxy-status.txt` (no agents proxies; `tag list` empty), the webhook selectors,
access log (403 lines have `-` for SNI and upstream; the 200s have the SNI), RBAC debug
(`requestedServerName: , ... ssl: none`, `enforced denied, matched policy none`).

Red herring: the JWT. The debug log shows `JWT token verification completed with: OK`, the
`sub` is the right service account, a failed `RequestAuthentication` returns **401** `Jwt
verification fails`, not 403, and the token is irrelevant to an ALLOW rule that matches on
`principals` (peer identity), not `requestPrincipals`.

## Fix (manifests)

- `manifests/namespaces.yaml`: agents -> `istio.io/rev: 1-27-1`, remove `istio-injection`.
- `manifests/mcp-tools/peerauthentication.yaml`: `mode: STRICT`. A future missing sidecar
  then fails as a connection reset at the transport layer, which is loud and unambiguous,
  instead of reaching the RBAC filter as an anonymous peer.

Live rollout:

```
kubectl label ns agents istio.io/rev=1-27-1 istio-injection-     # or let ArgoCD sync
kubectl -n agents rollout restart deploy/agent-runtime deploy/eval-runner
kubectl -n agents get pods                       # 2/2
istioctl proxy-status | grep agents              # SYNCED, 1.27.1
kubectl -n mcp-tools logs deploy/k8s-tools -c istio-proxy | grep 'POST /mcp'   # 200, SNI present
# only then apply STRICT on mcp-tools
```

Order matters: apply STRICT after agents have sidecars, or you turn a 403 into resets.

## Production follow-ups

- Upgrade runbook: before `istioctl uninstall --revision <old>`, list every pod still
  attached to the old revision and every namespace with `istio-injection`; block if any.
  `istioctl x precheck` and `istioctl proxy-status` give this.
- Policy as code (Kyverno/Gatekeeper or CI on the GitOps repo): reject `istio-injection`
  labels when ADR-017 applies; require pods in mesh namespaces to have `istio-proxy`.
- Alert: pods in namespaces labelled for the mesh without an `istio-proxy` container; MCP
  server 403 rate by `response_code_details`.
- Revision tags (`istioctl tag set prod --revision 1-27-1`) are the upstream-recommended way
  to avoid relabelling every namespace per upgrade; worth revisiting ADR-017.
- Keep the MCP server's own token validation: defence in depth when the mesh is misconfigured
  in the permissive direction.
