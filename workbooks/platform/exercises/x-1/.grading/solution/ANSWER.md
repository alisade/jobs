# ANSWER: platform/x-1 Zero-downtime maintenance strategy for the Tessellate GKE fleet

## Approach

Started from INC-3982's five failure modes and the quota file, then designed controls in the order
that removes the most risk: staffed windows and exclusions, one pool at a time, workload readiness
enforced by policy, then the fleet waves with traffic shifting.

## Fix

INC-3982 replayed under this design:
- Saturday unstaffed window: prod windows are Tue-Thu staffed; minors only when the pipeline lifts
  the standing "no minor upgrades" exclusion, so GKE cannot start a minor on its own.
- Pools in parallel: one pool at a time; stateful pool rolled node by node gated on search health.
- mdm-search red: gate on green and zero relocating shards between nodes.
- Singleton PDB blocking then forced eviction: rejected by the readiness policy; leader election
  and 2 replicas; pre-check fails the wave when disruptionsAllowed is 0.
- prod-green repeating it: one prod region at a time, 3-day soak, traffic shifted away first.

## Trade-offs / what I would do in production

- Blue-green for minors costs 144 vCPU for a few hours and a quota request; surge for patches.
- A 14-day stg soak slows minors but prod still stays well inside Stable's support window.
- Autopilot would remove most node toil but not the stateful and singleton problems.
- Measure: error budget used per upgrade, hours per cluster, readiness findings per team.
