# Reference: platform/w4-c1

The reference implementation is in `.grading/solution/fn/compose.go` and `reconcile.go`.

Key points:

- `validate` runs first and returns a field-path message. Bad input is a status condition
  (`ComposeFailed`), not an error: retrying cannot fix it, and the developer needs to see the message
  on their XR (`kubectl get appdatabase -n team-riq`). In a real XRD most of this is an OpenAPI schema
  with enums, so the API server rejects bad input before the function runs; the function still
  validates because schemas drift.
- A single `mk` closure builds every resource, so labels, namespace, deletion policy and provider
  config can never drift between the four resources.
- Reconcile lists by the composite label in the XR namespace (the fake treats `""` as all namespaces,
  which is exactly the bug the namespace-scoping test catches), builds a map by `Kind/name`, applies
  only what is missing or differs, and deletes anything labelled for this XR that is no longer desired.
- Ready is computed from observed state of the existing objects. A resource applied in this pass is
  not Ready yet, even if the apply succeeded.

Crossplane v2 judgement the answer should show:

- v2 XRs can be namespaced; new APIs should not use claims (kept for v1 compatibility). Developers
  get RBAC in their namespace and the composed MRs land in the same namespace.
- `ClusterProviderConfig` default: one platform-managed identity. A per-team namespaced
  `ProviderConfig` (in the team namespace, bound to a team GCP service account through Workload
  Identity) limits blast radius and makes cost attribution clean. Offer the override for that.
- `deletionPolicy: Delete` deletes the Cloud SQL instance when the XR is deleted. For prod use
  `Orphan` (or a composition variant that sets it) plus Cloud SQL deletion protection and backups.
