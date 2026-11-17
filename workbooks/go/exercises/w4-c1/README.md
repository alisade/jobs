# go/w4-c1 MCPServer reconciler: owned resources, conditions, finalizer

**Type:** coding | **Estimate:** 3 hours | **Week 4:** Build the capstone operator (Mon-Thu)

## Scenario

Lattice AI's platform team is building `agent-fleet-operator`, the Kubernetes control plane
for their agent platform on EKS. Product teams declare an `MCPServer` (group
`agents.example.dev`, `v1alpha1`) and expect a running, discoverable Model Context Protocol
server. The platform gateway discovers servers through a ConfigMap-backed registry,
`mcp-catalog` in `agent-system`; last month a hand-run script left stale entries there and
agents kept calling servers that no longer existed. The API types, CRD (with CEL validation
and defaults) and manager are done. The reconciler is yours.

## Task

Implement `internal/controller/mcpserver_controller.go`. Do not change `naming.go`,
the API types or the test suite fixture; the hidden tests rely on them.

## Requirements

1. **Owned children.** A `Deployment` and a `Service`, both named like the MCPServer, created
   and kept in sync with `controllerutil.CreateOrUpdate` and a **controller** owner reference.
   - Deployment: `replicas` from spec (default 1), selector and pod labels = `Labels(mcp)`,
     one container named `ContainerName` with the image, a container port named `PortName`
     on `spec.port`, env `MCP_TRANSPORT`, `MCP_PATH`, `MCP_PORT`, and `spec.envFrom`.
   - Service: selector `Labels(mcp)`, one port named `PortName` on `spec.port` targeting the
     container port.
2. **Drift.** Manual edits to children (`kubectl set image`, `kubectl scale`, deleting the
   Service) are reverted. That needs watches on the children, not just on `MCPServer`.
3. **Catalog.** Register `Endpoint(mcp)` under `CatalogKey(mcp)` in the `mcp-catalog`
   ConfigMap in `CatalogNamespace` (create the ConfigMap if absent; never clobber other
   servers' keys). Keep the entry current when port or path changes.
4. **Finalizer.** Add `FinalizerName`. On deletion, remove the catalog entry, then remove
   the finalizer. A missing catalog or missing entry must not block deletion.
5. **Status.** `observedGeneration`, `endpoint`, `availableReplicas` (from the Deployment
   status), and conditions via `meta.SetStatusCondition`, each with a non-empty `reason`
   and `observedGeneration`:

   | available vs desired | Ready | Progressing | Degraded |
   |---|---|---|---|
   | available >= desired | True | False | False |
   | 0 < available < desired | False | True | False |
   | available == 0 < desired | False | True | True |

6. **Steady state is quiet.** Reconciling an object whose state has not changed must not
   write to the API server (no status update when nothing changed). This is what keeps an
   operator from hot-looping at 2,000 objects.
7. A request for an object that no longer exists returns `ctrl.Result{}` and no error.
8. Emit Events for meaningful transitions (registered, deregistered, ready / not ready).
   `r.Recorder` is a `k8s.io/client-go/tools/events.EventRecorder` and may be nil in unit
   tests.
9. Add RBAC markers for everything the controller touches.

## Acceptance criteria

- `make test` passes (envtest: a real kube-apiserver and etcd, no kubelet and no
  Deployment controller, so tests set `Deployment.status` by hand).
- Hidden envtest tests cover owner refs, the generated spec, drift, recreation of deleted
  children, spec changes, all three condition states, observedGeneration, catalog
  registration and update, finalizer add/remove, deletion with a missing entry, NotFound,
  and a no-op steady state.
- No `time.Sleep` in the reconciler; errors returned (not swallowed) so the work queue backs off.

## How to run

```
make setup      # modules + envtest binaries for k8s 1.37 (cached in your user dir)
make test       # visible test
make manifests  # regenerate CRD and RBAC after changing markers
TEST_VERBOSE=1 make test   # controller logs
```

No cluster, Docker or kind is needed.

## What to submit

Your `internal/controller/mcpserver_controller.go` (plus any helper files you add in that
package) and `ANSWER.md`, then `/grade go/w4-c1`.

## Study-guide links

- API conventions, status and conditions: https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md#typical-status-properties
- controllerutil (CreateOrUpdate, owner refs, finalizers): https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/controller/controllerutil
- Kubebuilder: using finalizers: https://book.kubebuilder.io/reference/using-finalizers
- envtest reference: https://book.kubebuilder.io/reference/envtest
