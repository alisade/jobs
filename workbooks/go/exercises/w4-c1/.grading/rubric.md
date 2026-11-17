# Rubric: go/w4-c1 MCPServer reconciler: owned resources, conditions, finalizer
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Reconcile correctness and idempotency | 15 | Full: level-triggered (never depends on the triggering event), early return on NotFound, finalizer handled before anything else on deletion, errors returned for backoff instead of manual requeues or sleeps, selector set only on create, no status write when nothing changed. Partial: works but with redundant writes, Requeue loops or swallowed errors. Zero: edge-triggered logic or panics. |
| 3 | Ownership and watches | 10 | Full: `SetControllerReference` on both children, `Owns(&appsv1.Deployment{})` and `Owns(&corev1.Service{})`, mutate function only touches fields the operator owns (keeps defaulted / injected fields). Partial: owner refs without Owns, or clobbers whole spec. Zero: no owner refs. |
| 4 | Status and conditions | 10 | Full: `meta.SetStatusCondition` with meaningful reasons/messages, observedGeneration on status and each condition, status subresource used, table in README honoured. Partial: conditions present but reasons empty or generation missing. Zero: none. |
| 5 | External cleanup and RBAC | 5 | Full: catalog update preserves other keys, relies on optimistic concurrency (conflict -> requeue), deregistration tolerant of missing ConfigMap/entry, RBAC markers for deployments, services, configmaps, events. Partial: one gap. Zero: finalizer can hang deletion forever. |
| 6 | ANSWER.md and design judgement | 10 | Full: explains idempotency and the steady-state rule, compares CreateOrUpdate with server-side apply, names the scaling risk of a single ConfigMap catalog (1 MiB limit, write contention) and a better design. Partial: generic. Zero: empty. |
Total: 100
