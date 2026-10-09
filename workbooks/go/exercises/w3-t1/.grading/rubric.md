# Rubric: go/w3-t1 tenant-operator crash-loops after the v0.4.0 rollout
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: `Owns(&corev1.Secret{})` creates a cluster-wide Secret informer that needs `list` and `watch`; the `+kubebuilder:rbac` marker for secrets only grants get/create/update/patch/delete, so the reflector's LIST is forbidden, the cache never syncs, the controller fails after CacheSyncTimeout (2 min) and the manager exits -> CrashLoopBackOff; no controller means no reconcile for any Tenant. Partial: "missing RBAC for secrets" without the informer/cache-sync mechanism. Zero: blames NetworkPolicy, leader election or throttling. |
| 3 | Evidence | 15 | Full: quotes the forbidden LIST and the cache-sync timeout, ties the 2 minute run time to CacheSyncTimeout, shows the marker vs the generated role (or `kubectl auth can-i list secrets --as=system:serviceaccount:tenant-system:tenant-operator` returning no), and explains why envtest in CI (admin client) and dev (broad ClusterRole) passed. Partial: some of these. Zero: none. |
| 4 | Red herrings dismissed with reasons | 10 | Full: NetworkPolicy/lease timeouts ruled out because the same pod gets HTTP 403 responses from the apiserver (connectivity works) and acquires the lease; client-side throttling is a 1s delay, not a failure. Partial: ignored without reasons. Zero: "fixed" the NetworkPolicy. |
| 5 | Fix quality | 10 | Full: marker changed to add `list;watch` (keeping Owns), `make manifests` run, role.yaml committed; no wildcards. Partial: hand-edited role.yaml only, or removed `Owns(Secret)` (breaks SEC-2291). Zero: cluster-admin or `*`. |
| 6 | Production follow-up | 10 | Full: run envtest as the operator's SA with the generated role (as the grader does) or an e2e on kind with real RBAC; CI check that `make manifests` leaves no diff; cache Secrets only with the managed-by label (`cache.Options.ByObject` label selector) to limit cluster-wide Secret reads and memory; alert on cache-sync errors. Partial: one point. Zero: none. |
Total: 100
