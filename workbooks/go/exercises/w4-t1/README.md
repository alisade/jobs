# go/w4-t1 The operator that set the control plane on fire

**Type:** troubleshooting | **Estimate:** 2 hours | **Week 4:** Build the capstone operator (Tue reconcile, Fri scale)

## Scenario

Lattice AI runs `agent-fleet-operator` on `eks-prod-use1-agents`, managing 2,140
`MCPServer` objects. Since ArgoCD rolled out v0.3.1 two days ago, the platform on-call has
been paged for API server latency, the operator is pinned at its CPU limit, and the EKS
control plane team is asking why one service account dominates the `workload-low` APF
priority level. No MCPServer spec has changed. The on-call already tried raising the client
QPS; it made things worse. Read `artifacts/PAGE.md` first.

You have the operator source exactly as shipped in v0.3.1, the production artifacts in
`artifacts/`, and an envtest harness (real kube-apiserver + etcd) that runs the same
controller locally.

## Task

1. Find the root cause. Use the artifacts and reproduce it locally (`make test` contains a
   reproduction that measures the steady-state reconcile rate).
2. Fix the operator in `internal/controller/` (and `cmd/main.go` if you think it needs it).
   The portal still reads `status`; do not delete fields from the CRD in this release.
3. Write `ANSWER.md`: root cause with evidence from the artifacts and from your
   reproduction, the fix, why raising QPS did not help, and how you would prevent a repeat.

## Acceptance criteria

- At steady state (servers Ready, nothing changing) the controller does (almost) no
  reconciles and no writes to `MCPServer` objects.
- Calling `Reconcile` on an unchanged, Ready object is a no-op on the API server.
- Spec changes still roll out, drift on owned Deployments is still corrected, and
  `Ready`/`Degraded` still follow the Deployment's available replicas.
- `ANSWER.md` explains the feedback loop end to end and backs it with specific lines from
  the artifacts.

## How to run

```
make setup        # modules + envtest binaries for k8s 1.37
make test         # includes TestReproSteadyStateReconcileRate (fails while the bug is present)
TEST_VERBOSE=1 go test -v -count=1 ./internal/controller/ -run Repro   # with controller logs
                  # (prefix KUBEBUILDER_ASSETS=$(go tool setup-envtest use 1.37.0 -i -p path))
```

No cluster, Docker or kind is needed.

## What to submit

Your changes under `internal/controller/` (and `cmd/` if any) plus `ANSWER.md`, then
`/grade go/w4-t1`. Grading weighs the root-cause explanation and evidence more than the
patch.

## Study-guide links

- controller-runtime pkg/reconcile: https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/reconcile
- API conventions, status and conditions: https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md#typical-status-properties
- API Priority and Fairness: https://kubernetes.io/docs/concepts/cluster-administration/flow-control/
- Kubebuilder: good practices: https://book.kubebuilder.io/reference/good-practices
