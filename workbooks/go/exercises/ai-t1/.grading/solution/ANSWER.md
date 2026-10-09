# go/ai-t1 ANSWER (model)

## Approach

The 403 body `RBAC: access denied` comes from Envoy's RBAC filter, so I started at the
server sidecar: access log, then the RBAC debug log, then compared the denied request with
what the ALLOW policy requires. That pointed at the caller's identity, so I checked the
caller pods, the namespace labels and the installed injector webhook, and lined it up with
the upgrade change record and the Karpenter event.

## Root cause

`agents` still has `istio-injection=enabled` (`kubectl get ns`: ISTIO-INJECTION enabled,
REV empty). The injector that served that label was the 1.25 default revision, uninstalled
in CHG-7781 step 3; there is no default tag (`istioctl tag list`: none). The remaining
1-27-1 webhook requires `istio-injection DoesNotExist`. When Karpenter recreated the agent
pods at 06:40 they came up without a sidecar (`READY 1/1`, no istio-proxy, absent from
`proxy-status`). Their plaintext calls are accepted by PERMISSIVE mTLS but carry no
principal: RBAC debug shows `requestedServerName: , ... ssl: none` then `enforced denied,
matched policy none`; the access log 403s have `-` for SNI while the 200s before 06:40 have
`outbound_.8080_._.k8s-tools...`. The ALLOW policy needs principal
`cluster.local/ns/agents/sa/agent-runtime`, so nothing matches.

It did not fail at 19:10 because the old pods kept their 1.25 sidecars, cached config and
certificates until they were replaced.

Not the JWT: `JWT token verification completed with: OK` in the debug log, a JWT failure
would be a 401, and the policy matches on peer principals, not request principals.

## Fix

- `manifests/namespaces.yaml`: agents `istio.io/rev: 1-27-1`, `istio-injection` removed.
- `manifests/mcp-tools/peerauthentication.yaml`: STRICT.
- Rollout: label (ArgoCD sync), `rollout restart` agent-runtime and eval-runner, confirm 2/2
  and proxy-status, confirm 200s with SNI in the k8s-tools access log, then apply STRICT.
  `make test` shows 200 over mTLS for POST/GET/DELETE.

## Trade-offs / what I would do in production

- Pre-uninstall gate in the upgrade runbook: no pods on the old revision, no
  `istio-injection` labels.
- Admission policy rejecting `istio-injection` labels; alert on mesh-namespace pods without
  `istio-proxy`.
- Revisit ADR-017 in favour of revision tags so upgrades do not need namespace relabels.
