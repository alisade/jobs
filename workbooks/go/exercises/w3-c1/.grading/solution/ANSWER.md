# go/w3-c1 ANSWER (model)

## Approach

Followed the sample-controller shape: informers feed handlers, handlers enqueue
`namespace/name` keys for ConfigMaps, workers pull keys and reconcile from the listers.
Deployments enqueue the ConfigMaps they reference so new Deployments converge too.

## Fix

- Handlers: label filter, resync skip, tombstone unwrap, type-assert with `ok`.
- `reconcile`: lister Get; NotFound -> remove annotation; unlabelled -> no-op; otherwise
  hash and JSON-merge-patch every referencing Deployment whose annotation differs.
- `processNextItem`: Forget on success, AddRateLimited below MaxRetries, Forget + log when
  dropping, Done always.
- `Run`: `WaitForNamedCacheSyncWithContext`, N workers with `wait.UntilWithContext`, shut
  down the queue and wait for workers on cancel.
- `HashConfigMap`: SHA-256 over sorted, length-prefixed keys/values for Data and BinaryData.

## Trade-offs / what I would do in production

- Indexer on referenced ConfigMap names instead of List per reconcile.
- Leader election, Prometheus metrics for queue depth/retries/patches.
- Rate-limit rollouts when one ConfigMap fans out to many Deployments.
- Secrets support behind a separate flag and RBAC; never log values.
