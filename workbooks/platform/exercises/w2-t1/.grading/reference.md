# Reference: platform/w2-t1 prod-blue node pool upgrade stuck

Root cause: `k8s/riq/pdb.yaml` selects `app: riq-api`. The RIQ canary Deployment (added Monday) also
labels its pods `app: riq-api` so the Service sends it traffic, and its pod crash-loops (missing
RIQ_MODEL_BUCKET). For a `maxUnavailable` budget the Eviction API uses expectedPods = scale of the
controllers owning the matching pods = 4 (riq-api) + 1 (canary) = 5, desiredHealthy = 5 - 1 = 4,
currentHealthy = 4 Ready pods, disruptionsAllowed = 0. The unready canary pod has used the only
disruption, so no stable pod can be evicted: `riq-api-5d8f9c7b6-2hwkt` on p3x9 gets FailedEviction and
the surge upgrade waits on that node. The canary pod itself was evictable (IfHealthyBudget:
currentHealthy 4 >= desiredHealthy 4), which is why it was killed and rescheduled 54 minutes ago.

Red herring: the quota warning. Both surge nodes were created and became Ready.

Fix (`.grading/solution/k8s/riq/pdb.yaml`): scope the selector to the stable track with
`matchExpressions: [{key: track, operator: NotIn, values: [canary]}]` (or add `track: stable` to the
stable pod template and select on it), keep `maxUnavailable: 1`; optionally add
`unhealthyPodEvictionPolicy: AlwaysAllow` so unready pods never hold a drain. Result: expected 4,
desired 3, healthy 4, one disruption allowed; with two stable pods down the drain still stops.

Mitigation in the incident: have RIQ scale `riq-api-canary` to 0 (or roll it back); the budget recovers
to one disruption immediately and the drain continues. Do not delete the PDB, cancel the upgrade without
a plan, or `kubectl drain --disable-eviction`.

Prevention: chart convention for PDB selectors, a CI check for budgets that match pods of several
controllers, alert on disruptionsAllowed == 0 before a maintenance window, canary health gate, and
consider blue-green for this pool so a stuck drain does not leave the pool half upgraded.
