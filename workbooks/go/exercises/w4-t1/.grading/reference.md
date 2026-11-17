# Reference: go/w4-t1 hot reconcile loop

Injected fault: `internal/controller/mcpserver_controller.go` writes
`status.lastReconcileID = controller.ReconcileIDFromContext(ctx)` on every reconcile, and
`For(&MCPServer{})` has no predicate. Each reconcile writes status, each status write is a
watch event, each event is a reconcile. Reference fix:
`.grading/solution/internal/controller/mcpserver_controller.go`.

Red herrings: client-side throttling log lines, APF queueing in `workload-low`, the
controller-runtime bump in the same release, 409 conflicts.

## What the hidden tests check

| Test | Catches |
|---|---|
| NoHotLoopAcrossManyServers | reconcile_total delta over 3s for 5 Ready servers <= 3 |
| SteadyStateNoStatusWrites | resourceVersion constant over 2s |
| DirectReconcileIsNoOp | predicate-only fixes (status still written per reconcile) |
| SpecChangeStillReconciles / ChildDriftStillCorrected | over-eager predicates that drop real events |
| DeploymentStatusStillDrivesReady | global `WithEventFilter(GenerationChangedPredicate{})` |
| StatusStillComplete | deleting status fields instead of fixing the write |

Expected outcomes: correct fix 8/8; predicate-only 7/8; global event filter fails nearly
everything because servers never become Ready.

## Interview angles

- Why does `GenerationChangedPredicate` not see status changes? (status subresource writes
  do not bump `metadata.generation` for CRDs with the status subresource enabled.)
- What else produces this loop? `lastTransitionTime: metav1.Now()` set by hand with
  sub-second precision types, unsorted slices built from map iteration, a mutate function
  that rewrites server-defaulted fields so every CreateOrUpdate is an Update.
- How does the work queue dedupe keep this from being even worse, and why does it not
  save you?
