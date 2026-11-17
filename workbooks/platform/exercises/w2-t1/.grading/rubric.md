# Rubric: platform/w2-t1 prod-blue node pool upgrade stuck at 1 of 6 nodes
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: the riq-api PDB (`maxUnavailable: 1`, selector `app: riq-api`) also matches the RIQ canary pod, which carries `app: riq-api` and is crash-looping. With maxUnavailable, expected pods come from the owning controllers' scale (4 + 1 = 5), so desiredHealthy = 4; currentHealthy = 4 (the canary is not Ready); disruptionsAllowed = 0. The unready canary pod consumes the whole budget, so no stable pod can be evicted and the drain of p3x9 waits. Partial (10-15): "the PDB allows 0" without the selector overlap or the maxUnavailable arithmetic. Zero: quota, surge node, or "PDB too strict" without the canary. |
| 3 | Evidence | 20 | Full: quotes PDB status (`expectedPods 5, desiredHealthy 4, currentHealthy 4, disruptionsAllowed 0`), the pods list with the canary CrashLoopBackOff and its labels, FailedEviction events on riq-api-2hwkt, the simulator output. Partial: one or two. Zero: assertion only. |
| 4 | Red herring handled | 5 | Rules out quota: surge nodes s1u1 and s2u2 were created and Ready; the warning is informational. |
| 5 | Fix quality and mitigation | 10 | Full: PDB scoped to the stable track (matchExpressions `track NotIn [canary]`, or `track: stable` added to the stable pod template with matchLabels), budget kept at one disruption; mitigation: ask RIQ to scale the broken canary to 0 or roll it back (its log shows a missing RIQ_MODEL_BUCKET), which unblocks the drain at once; not deleting the PDB, not cancelling the upgrade blind, not force-draining. Mentions `unhealthyPodEvictionPolicy: AlwaysAllow` and why it alone does not fix this (the blocked pods are Ready). |
| 6 | Prevention | 10 | Concrete: platform chart convention that PDB selectors include the track, a CI policy that flags PDBs matching pods of more than one controller, canary readiness gate before it can join the Service, alert on `disruptionsAllowed == 0` for longer than N minutes before a window, consider blue-green for this pool. |
Total: 100
