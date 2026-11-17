# go/w4-c1 ANSWER (model)

## Approach

Reconcile is level-triggered: every run reads the MCPServer, computes the full desired
state, and converges children, catalog and status, so any event (create, child drift,
resync) produces the same result. Order: NotFound -> deletion path -> finalizer ->
children -> catalog -> status. Tested with envtest, setting Deployment status by hand
because envtest runs no controllers.

## Fix

- `CreateOrUpdate` for Deployment and Service with `SetControllerReference`; the mutate
  function only sets fields the operator owns, sets the selector once (immutable), and
  replaces only the `mcp-server` container so injected sidecars and server-defaulted
  fields survive (otherwise every reconcile is an update).
- `Owns(Deployment)`, `Owns(Service)` so drift and deletion of children enqueue the owner.
- Catalog: get-or-create the `mcp-catalog` ConfigMap, upsert one key, `Update` with the
  read resourceVersion so concurrent writers conflict and retry instead of losing keys.
- Finalizer: deregister (tolerating NotFound) then `RemoveFinalizer` + `Update`.
- Status: compute conditions with `meta.SetStatusCondition` (which only moves
  `lastTransitionTime` on a flip), compare with the previous status, and call
  `Status().Update` only on a real change.
- Events via the `events.k8s.io` recorder on registration, deregistration and Ready flips.

## Trade-offs / what I would do in production

- Server-side apply with a field manager would remove the "preserve defaulted fields"
  bookkeeping and make ownership explicit; CreateOrUpdate is simpler to read and test.
- A single ConfigMap catalog is a contention point and caps at 1 MiB; at fleet scale use a
  per-server object (e.g. an `MCPCatalogEntry` CR or EndpointSlice-style labels) that the
  gateway lists, so there is no shared write hot spot.
- Next: defaulting/validating webhook, HPA and PDB, `Degraded` driven by min-available,
  metrics on reconcile errors, `MaxConcurrentReconciles` tuning.
