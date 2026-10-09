# go/w4-t1 ANSWER (model)

## Approach

Started from the rates, not the logs. `operator-metrics.txt`: reconcile_total grows ~41,900
per minute (~700/s) for 2,140 objects whose specs did not change (v0.2.4 did 17/min).
`apiserver-metrics.txt`: ~697 PUT/s on `mcpservers/status`, zero Deployment writes, zero
spec writes. So the operator is reconciling constantly and the only thing it writes is
status. Then looked at what the status writes contain (audit RequestResponse) and at what
changed between v0.2.4 and v0.3.1 (`git-log.txt`).

## Root cause

A self-sustaining status feedback loop introduced by commit 41d07e3 (PLAT-2291):

1. `Reconcile` sets `status.lastReconcileID = controller.ReconcileIDFromContext(ctx)`. The
   ID is a fresh UUID every run, so the `reflect.DeepEqual(before, after)` guard is never
   true and every reconcile ends in `Status().Update`.
2. Each status update bumps `resourceVersion` and produces a watch event. `For(&MCPServer{})`
   has no predicate, so the Update event re-enqueues the same object.
3. Goto 1. Every object loops forever at the speed the client rate limiter allows.

Evidence:
- `audit-excerpt.jsonl`: consecutive `update` calls on `.../github-tools/status`, ~10-30 ms
  apart, by `system:serviceaccount:agent-system:agent-fleet-operator`; the request bodies
  are identical except `status.lastReconcileID`; `generation` stays 3 while
  `resourceVersion` climbs 88412907 -> 88413391 within a second.
- `mcpserver-github-tools.yaml`: managedFields shows `manager` owning `f:lastReconcileID` on
  the status subresource with a timestamp of "now"; spec last applied by ArgoCD on 09-30.
- `controller-logs.txt`: every `reconciled` line says deployment/service `unchanged`
  (`grep -vc` = 0), and the 409 conflicts are the loop racing its own cache.
- PUT status rate (697/s) == reconcile rate (~698/s): one write per reconcile.
- Local repro (envtest): `TestReproSteadyStateReconcileRate` reported 2,708 reconciles in 3s
  for one unchanged object before the fix, 0 after.

## Fix

- Stop writing `lastReconcileID` to status. Status must be a pure function of observed
  state; the reconcileID is already on every log line (controller-runtime injects it into
  the logger), which is what support needed. The field stays in the CRD (deprecated) so
  the portal does not break; it simply stops changing.
- Defense in depth: `For(&MCPServer{}, builder.WithPredicates(predicate.Or(
  GenerationChangedPredicate{}, LabelChangedPredicate{}, AnnotationChangedPredicate{})))`.
  Scoped to `For` only: a global `WithEventFilter(GenerationChangedPredicate{})` would also
  drop Deployment status events (availableReplicas does not bump generation), and Ready
  would never follow availability.
- The predicate alone is not enough: every legitimate reconcile (resync, child event,
  restart of 2,140 objects) would still write status. Verified with the hidden-test style
  check: calling `Reconcile` 5 times on a Ready object leaves `resourceVersion` unchanged.
- Log "children reconciled" only when something changed; the per-reconcile Info line was
  ~42k lines/min of noise.
- Reverted QPS/Burst to 20/30.

## Trade-offs / what I would do in production

- Why QPS made it worse: the client-side limiter was the only back-pressure on the loop.
  Raising it let the same loop push ~5x more PUTs into the API server and etcd (p99 PUT
  1.9s, APF queueing in `workload-low`, +380 MiB etcd history). Throttling and APF were
  symptoms of the loop, not causes.
- Guard rails: keep the steady-state envtest (reconciles and resourceVersion over a window)
  in CI; alert on `rate(controller_runtime_reconcile_total) / object_count` and on PUT
  `mcpservers/status` rate; review rule "no timestamps, IDs or unordered collections in
  status"; dedicated FlowSchema + PriorityLevelConfiguration so a misbehaving operator
  cannot starve other workloads.
- Rollout: ship as v0.3.2 through ArgoCD; reconcile rate should drop to the resync baseline
  within one resync period.
