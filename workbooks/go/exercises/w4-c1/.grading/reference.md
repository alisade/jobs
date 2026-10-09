# Reference: go/w4-c1 MCPServer reconciler

Reference implementation: `.grading/solution/internal/controller/mcpserver_controller.go`.

## What the hidden tests force

| Test | Forces |
|---|---|
| ChildrenHaveControllerOwnerRefs | `SetControllerReference` (controller=true, blockOwnerDeletion=true) |
| DeploymentDriftIsCorrected / ServiceDeletedIsRecreated | `Owns()` watches; drift on a child enqueues the owner |
| SpecChangeUpdatesChildren | mutate function re-applies spec on every reconcile |
| NotReady / Ready tests | the condition table, `availableReplicas` read from the Deployment |
| ObservedGenerationTracksSpec | `observedGeneration` on status and on every condition |
| Catalog / Delete tests | ConfigMap upsert that keeps other keys; finalizer that never hangs |
| SteadyStateDoesNotRewriteStatus | compare before/after and skip `Status().Update` when equal |

## Pitfalls seen in real operators

- Mutate function that rebuilds `Spec.Template.Spec` from scratch: the API server defaults
  `terminationMessagePath`, `imagePullPolicy`, `dnsPolicy` and friends, so the object
  never compares equal and every reconcile is an Update, which (with `Owns`) re-triggers
  the reconcile: a slow hot loop. Keep defaulted fields, or use server-side apply.
- Setting `lastTransitionTime` yourself to `time.Now()` on every reconcile: same hot loop
  via status. `meta.SetStatusCondition` only changes it when the status flips.
- `Requeue: true` after success "to be safe": burns the queue; rely on watches.
- Removing the finalizer before external cleanup succeeded: leaks catalog entries.
- Treating NotFound of the catalog as an error during deletion: the object can never be
  deleted (finalizer stuck), which is the w4 troubleshooting classic.

## Interview angles

- Why level-triggered? What happens if the controller is down while three edits land?
- CreateOrUpdate vs server-side apply: field ownership, conflicts with HPA on `replicas`.
- How would you avoid the catalog ConfigMap becoming a hot spot at 5,000 servers?
