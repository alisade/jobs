# Reference: go/w3-t1 tenant-operator RBAC incident

## Root cause

v0.4.0 (commit 3f08d6e) added `Owns(&corev1.Secret{})`. In controller-runtime, every
`For`/`Owns`/`Watches` type gets a shared informer from the manager's cache, and an informer
starts with a cluster-scoped LIST then WATCH (the manager is not namespace-restricted). The
RBAC markers were not updated:

```
// +kubebuilder:rbac:groups="",resources=secrets,verbs=get;create;update;patch;delete
```

so the generated `manager-role` lacks `list` and `watch` on secrets. The reflector logs
`secrets is forbidden ... cannot list resource "secrets" ... at the cluster scope` and keeps
retrying with backoff. The controller waits for all its sources to sync; after
`CacheSyncTimeout` (default 2 minutes - matching 09:37:58 -> 09:39:58 in the logs) it
returns `timed out waiting for cache to be synced for kind source: *v1.Secret`, the manager
stops and the process exits 1. Kubelet restarts it -> CrashLoopBackOff. Because the
controller never starts its workers, no Tenant is reconciled, not just Secret-related work.
Existing Tenants look fine because their children already exist.

## Why nothing caught it

- envtest in CI uses the admin rest.Config from `testEnv.Start()` (system:masters), so RBAC
  is never exercised.
- Dev binds the default SA to a broad `platform-dev-admin` ClusterRole.
- Only prod uses the generated `manager-role`.

## Red herrings

- Lease `context deadline exceeded` on the standby pod and the egress NetworkPolicy: the
  crashing pod acquires the lease and receives HTTP 403 responses from the apiserver, so the
  network path is fine.
- `client-side throttling` is a 1 second client QPS wait, informational.

## Fix

```
// +kubebuilder:rbac:groups="",resources=secrets,verbs=get;list;watch;create;update;patch;delete
```

then `make manifests` and commit `config/rbac/role.yaml`. Removing `Owns(Secret)` "fixes" the
crash but breaks SEC-2291 (a deleted Secret is no longer restored).

## Production follow-ups

- Test with the real identity: `testEnv.AddUser` + bind the generated ClusterRole (what the
  grader does), or e2e on kind with the kustomize RBAC.
- CI: `make manifests && git diff --exit-code`.
- Reduce blast radius of cluster-wide Secret read: `cache.Options{ByObject: {&corev1.Secret{}:
  {Label: managed-by=tenant-operator}}}` so the informer only lists the operator's Secrets
  (RBAC still needs list/watch, but memory and exposure shrink); or namespace-scoped Roles if
  tenants live in known namespaces.
- Alert on `controller_runtime_*` absence / CrashLoopBackOff of operators, and on
  ArgoCD Degraded after sync.
