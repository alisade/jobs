# go/w3-c1 A client-go config reloader: informers and a rate-limited work queue

**Type:** coding | **Estimate:** 3 hours | **Week 3:** client-go informers, listers, work queues

## Scenario

Lumen Pay runs ~400 Deployments on EKS. Teams change feature flags and connection
settings in ConfigMaps, then forget to restart the pods, and the incident review for last
month's ledger outage found pods running 9-day-old config. The platform team will not take a
third-party reloader into the payments clusters, so you are writing a small in-house one with
plain client-go (no controller-runtime) so every moving part is visible to reviewers.

The contract:

- A ConfigMap opts in with the label `reloader.lumenpay.io/watch: "true"`.
- A Deployment opts in with the annotation `reloader.lumenpay.io/configmaps: "a, b"` (names of
  ConfigMaps in its own namespace).
- The controller keeps the pod template annotation `cm.reloader.lumenpay.io/<configmap>` equal
  to the ConfigMap's content hash. Changing a pod template annotation makes the Deployment
  controller roll the pods; that is the whole trick.

## Task

1. Implement the TODOs in `reloader/controller.go`: event handlers, `Run`,
   `processNextItem`, `reconcile`, `HashConfigMap`. Keep the exported API and the
   unexported method names (the hidden tests call the handlers directly).
2. Fill in `ANSWER.md`.

`cmd/config-reloader/main.go` and `deploy/rbac.yaml` are done; read them.

## Requirements

1. The queue key is the ConfigMap's `namespace/name`. Handlers only enqueue; all API calls
   happen in `reconcile`, which reads from the listers (cache), never with live GETs.
2. ConfigMap add/update/delete events enqueue only watched ConfigMaps. Delete handlers must
   cope with `cache.DeletedFinalStateUnknown` tombstones and with unexpected types (ignore,
   do not panic). Periodic resyncs (same resourceVersion) need not enqueue.
3. Deployment add/update events enqueue every ConfigMap the Deployment references, so a
   newly created Deployment gets the current hash.
4. `reconcile` patches only Deployments in the ConfigMap's namespace that reference it, and
   only when the annotation differs from the hash (no write when converged, no hot loop from
   our own patch events). If the ConfigMap is gone, remove the annotation. If the label was
   removed, leave Deployments alone. Use a patch (merge, strategic merge, or apply), never a
   full `Update`; other pod template annotations must survive.
5. `HashConfigMap`: lowercase hex SHA-256 over `Data` and `BinaryData`, keys sorted,
   unambiguously delimited (`{"ab":"c"}` and `{"a":"bc"}` differ), metadata ignored.
6. Retry policy: on error `AddRateLimited` while `NumRequeues(key) < MaxRetries`, otherwise
   drop with `Forget` and log. On success `Forget`. Always `Done`. With `MaxRetries=3`, a
   permanently failing key is attempted exactly 4 times.
7. `Run(ctx, workers)`: wait for caches with the context; return `ErrCacheSync` if they never
   sync; start the workers; on cancellation shut the queue down, wait for workers, return
   nil.

## Acceptance criteria

- `make test` passes with `-race`; `go vet ./...` is clean.
- Hidden tests cover filtering, namespaces, idempotency, no hot loop, patch type, new
  Deployments, deletion and tombstones, retry and drop, shutdown, cache-sync failure, and
  hash properties.

## How to run

```
make setup
make test
```

The tests use `k8s.io/client-go/kubernetes/fake` with real shared informers; no cluster is
needed. `fake.Clientset.PrependReactor` is how the hidden tests inject API errors.

## What to submit

`reloader/controller.go` and `ANSWER.md`, then run `/grade go/w3-c1` from the workbooks root.

## Study-guide links

- Sample controller: https://github.com/kubernetes/sample-controller
- client-go under the hood: https://github.com/kubernetes/sample-controller/blob/master/docs/controller-client-go.md
- client-go `tools/cache`: https://pkg.go.dev/k8s.io/client-go/tools/cache
- client-go `util/workqueue`: https://pkg.go.dev/k8s.io/client-go/util/workqueue
