# go/w3-t1 ANSWER (model)

## Approach

Started from the crashing pod's `--previous` logs rather than the page. The process runs for
exactly two minutes, logs a forbidden LIST on secrets every few seconds, then a cache-sync
timeout and exits. Compared v0.3.2..v0.4.0: the only controller change is
`Owns(&corev1.Secret{})`. Compared that with the RBAC markers and `config/rbac/role.yaml`.

## Root cause

`Owns(&corev1.Secret{})` makes the manager start a cluster-wide Secret informer (LIST +
WATCH). The secrets marker grants `get;create;update;patch;delete` only, so the generated
`manager-role` has no `list`/`watch` on secrets:

```
failed to list *v1.Secret: secrets is forbidden: User "system:serviceaccount:tenant-system:tenant-operator"
cannot list resource "secrets" in API group "" at the cluster scope
...
09:39:58 Could not wait for Cache to sync ... timed out waiting for cache to be synced for kind source: *v1.Secret
09:39:58 ERROR setup problem running manager
```

09:37:58 -> 09:39:58 is the 2 minute default `CacheSyncTimeout`. The controller never starts
workers, so no Tenant is reconciled; the manager exits 1 -> CrashLoopBackOff.
`kubectl auth can-i list secrets -A --as=system:serviceaccount:tenant-system:tenant-operator`
would return `no` (from role.yaml, secrets rule has no list/watch).

CI missed it because envtest runs as the admin user; dev missed it because the operator
there runs with a broad admin ClusterRole.

Ruled out: the NetworkPolicy and the lease timeouts on the standby pod - the crashing pod
acquires the lease and gets 403 responses from the apiserver, so the network path works.
Client-side throttling is a 1s informational wait.

## Fix

Changed the marker to `verbs=get;list;watch;create;update;patch;delete`, ran
`make manifests`, committed the regenerated `config/rbac/role.yaml`. Verified with an envtest
that runs the manager as the SA bound only to the generated ClusterRole: Tenant goes Ready,
and deleting the storage Secret gets it recreated.

## Trade-offs / what I would do in production

- CI: envtest as the operator identity with generated RBAC; `make manifests` must leave no diff.
- Limit the Secret informer with a label selector via `cache.Options.ByObject`.
- Alert on operator CrashLoopBackOff and ArgoCD Degraded right after a sync.
