# Reference: go/w3-c1 config-reloader

Reference code: `.grading/solution/reloader/controller.go`.

## Key points

- **Keys, not objects, go on the queue.** Handlers turn events into `namespace/name` and
  return. Reconcile re-reads the lister, so it is level-based: a missed or coalesced event
  does not matter, and duplicate keys are deduplicated by the queue.
- **Two event sources, one key space.** Deployment events enqueue the ConfigMaps they
  reference, which is how a new Deployment gets the current hash without a second queue.
- **Convergence check before every write.** Our own patch produces a Deployment update
  event; it enqueues the ConfigMap again, reconcile sees the annotation already equals the
  hash, and stops. Without that check you have a hot loop.
- **Tombstones.** When a watch drops and the relist finds the object gone, the informer
  delivers `cache.DeletedFinalStateUnknown{Key, Obj}` with the last known state. Unwrap it.
- **Retry policy.** `AddRateLimited` gives per-item exponential backoff; `Forget` resets the
  item's failure count (forgetting to call it leaks memory in the limiter and keeps the
  backoff high forever); `Done` must always be called or the key is stuck "processing".
- **JSON merge patch with `null`** deletes a single annotation without touching others and
  without a resourceVersion precondition, so it never conflicts with the Deployment
  controller or HPA.
- **Hash.** Sorted keys plus length-prefixing removes both map-order nondeterminism and
  concatenation ambiguity.

## What a strong ANSWER.md adds

- Replace `List(labels.Everything())` + filter with a custom indexer
  (`cache.Indexers{"byConfigMap": ...}`) and `ByIndex`; at 400 Deployments per namespace the
  List is fine, at 10k it is not.
- Leader election (`client-go/tools/leaderelection`) for 2 replicas.
- A shared ConfigMap referenced by 200 Deployments rolls all of them at once: add a
  rollout budget or jitter.
- Secrets: same pattern, but RBAC `get/list/watch secrets` cluster-wide is sensitive; use a
  metadata-only informer plus targeted GETs, or namespace-scoped Roles.
