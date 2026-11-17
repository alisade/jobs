# ANSWER: platform/w4-c1 AppDatabase composition function and readiness

## Approach

Validation first, then one builder closure for all composed resources so shared fields cannot drift.
Reconcile diffs desired against observed by `Kind/name`, applies only on difference, prunes, and
derives Ready from observed conditions. Tested idempotency by counting fake writes across two runs.

## Fix

Implemented `Compose` (validation with field paths, four resource shapes, size/version maps, defaults)
and `Reconcile` (namespace-scoped list, apply-on-diff, prune, Synced/Ready conditions, wrapped errors).

## Trade-offs / what I would do in production

- Namespaced XR, no claim: v2 makes claims legacy; RBAC on the namespace is enough.
- ClusterProviderConfig default for simplicity; per-team ProviderConfig with Workload Identity for
  blast radius and cost attribution.
- Delete removes the instance with the XR; prod uses Orphan plus deletion protection and backups.
- Ship the composition as a versioned configuration package, test with crossplane render in CI, and
  roll new revisions to one namespace first.
