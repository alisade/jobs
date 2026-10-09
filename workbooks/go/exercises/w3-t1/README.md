# go/w3-t1 tenant-operator crash-loops after the v0.4.0 rollout

**Type:** troubleshooting | **Estimate:** 2 hours | **Week 3:** controller-runtime, Kubebuilder markers, envtest

## Scenario

Harbor Analytics runs a Kubebuilder operator, `tenant-operator`, on its EKS analytics
clusters. A `Tenant` gives a team a ResourceQuota and a storage Secret in its namespace.
ArgoCD rolled v0.4.0 to production this morning. New Tenants are not getting reconciled, one
operator replica is in CrashLoopBackOff, and a training pipeline is blocked. CI (envtest)
is green and "it works in dev".

Start with `incident/PAGE.md`; everything the on-call collected is in `incident/`. The
operator source is in this folder exactly as tagged v0.4.0.

## Task

1. Find the root cause. Explain it with evidence from the bundle and the code, including why
   CI and the dev cluster did not catch it. There is at least one red herring in the bundle.
2. Fix it in the source, the way this repo expects changes to be made, and keep the
   behaviour v0.4.0 was released for.
3. Fill in `ANSWER.md` (all four sections).

## Acceptance criteria

- With only the RBAC generated from the code's markers, the operator reconciles a new Tenant
  to `Ready=True` and creates its ResourceQuota and Secret.
- A deleted storage Secret is restored without anyone touching the Tenant (SEC-2291).
- The operator's ClusterRole stays least-privilege: no wildcards, no RBAC/escalation verbs,
  no cluster-admin.
- The committed `config/rbac/role.yaml` matches what the markers generate.

## How to run

```
make setup       # modules + envtest binaries (kube-apiserver, etcd), no Docker needed
make test        # unit + envtest; note it runs as cluster admin, exactly like CI
make manifests   # regenerate CRDs and config/rbac/role.yaml from the markers
```

`/grade` runs the operator in envtest as `system:serviceaccount:tenant-system:tenant-operator`
bound only to the ClusterRole regenerated from your markers.

## What to submit

Your source/manifest changes and `ANSWER.md`, then `/grade go/w3-t1` from the workbooks root.

## Study-guide links

- Kubebuilder markers reference (RBAC markers): https://book.kubebuilder.io/reference/markers
- controller-runtime `pkg/builder` (For / Owns / Watches): https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/builder
- envtest reference: https://book.kubebuilder.io/reference/envtest
- client-go under the hood (reflector list/watch): https://github.com/kubernetes/sample-controller/blob/master/docs/controller-client-go.md
