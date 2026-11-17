# ANSWER: platform/w2-t1 prod-blue node pool upgrade stuck at 1 of 6 nodes

## Approach

<!-- How you investigated: what you looked at first, what the simulator showed, what you ruled out. -->

## Root cause

<!-- The budget, its selector, the pods it matches, and the arithmetic. Quote kubectl output. Why the
quota warning is not it. -->

## Fix

<!-- What you changed in k8s/ and why it keeps the protection. How you verified it. The immediate
mitigation during the incident (before the GKE PDB timeout) and what you would not do. -->

## Trade-offs / what I would do in production

<!-- Prevention: PDB conventions in the platform chart, policy checks on overlapping selectors,
unhealthyPodEvictionPolicy, canary health gates, upgrade watchdog, blue-green for this pool. -->
