# ANSWER: platform/w2-t1 prod-blue node pool upgrade stuck at 1 of 6 nodes

## Approach

Events showed FailedEviction for riq-api-2hwkt on p3x9; `get pdb` showed riq-api with 0 allowed
disruptions. `make drain` reproduced it at the same node.

## Root cause

The riq-api PDB selects `app: riq-api`, which also matches the RIQ canary pod (labels app: riq-api,
track: canary), now CrashLoopBackOff. PDB status: expectedPods 5, desiredHealthy 4, currentHealthy 4,
disruptionsAllowed 0. With maxUnavailable: 1, expected comes from controller scale (4 + 1), so the unready
canary consumes the single disruption and no stable pod can be evicted. The quota warning is not it:
surge nodes s1u1 and s2u2 were created and Ready.

## Fix

PDB selector excludes the canary track (`track NotIn [canary]`), maxUnavailable stays 1, plus
unhealthyPodEvictionPolicy AlwaysAllow. Simulator: expected 4, desired 3, healthy 4, allowed 1; all nodes
drain. Immediate mitigation: RIQ scales the canary to 0 (its log shows a missing RIQ_MODEL_BUCKET), which
unblocks the drain before GKE's PDB timeout. Not deleting the PDB, not force-draining.

## Trade-offs / what I would do in production

Chart convention for PDB selectors, a CI policy flagging budgets that match pods of more than one
controller, an alert on disruptionsAllowed == 0 before a window, a canary readiness gate, and blue-green
for this pool.
