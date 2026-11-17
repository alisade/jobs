# Rubric: go/w5-t1 audit-sink rebalances in a loop after "static membership" rollout
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: all replicas share `group.instance.id=audit-sink` (literal env value; plus the constant `audit-sink-0` fallback in `FromEnv`), so each join replaces the previous static member, the coordinator fences it, `main` exits 1, the kubelet restarts it and it fences the next one; only one member ever owns all 6 partitions. Partial (10): "static membership is misconfigured" without the shared-id mechanism, or blames session timeout. Zero: CPU limit / throttling / HPA. |
| 3 | Evidence | 20 | Full: quotes at least three independent artifacts that prove it, e.g. broker "Replacing previously mapped member ... groupInstanceId=audit-sink", `FENCED_INSTANCE_ID` + exit 1 in pod logs, `#MEMBERS 1` with one consumer owning `agent.audit(0..5)`, identical `GROUP_INSTANCE_ID` in describe pod, processed/produced ratio > 1, plus the `make repro` output before and after. Partial: one or two artifacts. Zero: assertion without evidence. |
| 4 | Red herring handled | 10 | Full: explains why CPU throttling is a symptom (only the current owner of all 6 partitions is busy; the other two are idle at ~10m CPU) and why a longer session timeout makes things worse, not better. Partial: ignores it silently. Zero: raises CPU/session timeout as the fix. |
| 5 | Fix quality | 10 | Full: StatefulSet (stable ordinal names) with `GROUP_INSTANCE_ID` from `fieldRef: metadata.name`, HPA retargeted, PDB intact, static membership kept; `FromEnv` falls back to `POD_NAME` and errors instead of using a constant. Partial: Deployment + `metadata.name` (unique but changes every rollout, so departed static members hold partitions until session timeout) or disabling static membership. Zero: no fix. |
| 6 | Production follow-up | 5 | Full: rollout plan (Deployment to StatefulSet migration, orphaned static members expire after session timeout or are removed with an admin LeaveGroup), duplicate handling for compliance (idempotent index by event id), an alert on members < replicas. Partial: generic. |
Total: 100
