# Design: zero-downtime maintenance strategy for the Tessellate GKE fleet

## Context, goals and non-goals

"Zero downtime" here means: a planned upgrade of any cluster burns no more than 10% of a service's
28-day error budget (RIQ: 2 of its ~20 minutes) and never takes two prod regions down at once.
INC-3982 failed on five points: an unstaffed window, two node pools draining in parallel, a
stateful workload drained faster than it can heal, a singleton whose PDB allows zero disruptions,
and no gate between prod-blue and prod-green.

In scope: control plane and node upgrades for the four clusters and the ten planned for 2027, plus
the add-ons that move with Kubernetes versions (Crossplane, ingress, GMP agents). Out of scope:
application releases (Argo CD waves already exist) and OS-level patching outside GKE node images.

## Version and channel strategy

| Cluster | Channel | Why |
|---|---|---|
| dev-1 | Regular | sees a version weeks before prod |
| stg-1 | Regular | same version as dev, with prod-like pools; the soak target |
| prod-blue, prod-green | Stable | versions that have soaked in Regular |
| PCI clusters (2027) | Stable, consider Extended | longer support window, fewer forced minors during audits |
| load-test clusters (2027) | Rapid | earliest warning; ephemeral |

Version flow per minor (for example 1.34): available on Regular -> dev-1 auto -> stg-1 (in its
Tue-Thu window) -> 14 days soak with the readiness report clean -> prod-green -> 3 business days ->
prod-blue. The platform team pins the target version per wave in a versions file in Git; the
upgrade pipeline reads it, so humans decide minors and GKE handles patches inside windows.

Skew: the Kubernetes skew policy lets nodes lag the control plane by a bounded number of minors,
but every minor of lag is a future double upgrade. Rule: node pools at most one minor behind, and
they catch up before the control plane moves again. prod-blue (control plane 1.33, nodes 1.32)
gets its 1.33 node upgrade in the next staffed window, before Stable offers 1.34.

## Maintenance windows and exclusions

- Prod windows move from Sat-Sun 06:00-12:00 to Tue-Thu 14:00-20:00 UTC, when the platform team is
  staffed and both on-call shifts overlap the team. prod-green Tue-Wed, prod-blue Wed-Thu, so the
  two never share a window. Windows must still meet GKE's minimum availability over the rolling
  period; Tue-Thu 6 h each is comfortably above it.
- stg-1 keeps Tue-Thu 14:00-18:00; dev-1 gets Mon-Fri 14:00-20:00 (no more "any time").
- Exclusions (set in Terraform, not by hand), checked against current scope limits:
  - quarter-end (7 business days): "no minor or node upgrades" on prod;
  - Black Friday to Cyber Monday: "no upgrades" (well within its maximum length);
  - year-end freeze 12-18 to 01-04 (18 days): "no upgrades"; if a security patch is required, CAB
    removes the exclusion for one window.
  - A standing "no minor upgrades" exclusion on prod so minors only happen when the pipeline
    deliberately lifts it for the planned wave; patches still flow in windows.
- GKE cluster notifications (Pub/Sub: upgrade available, scheduled, started, finished) feed a small
  function that posts to the platform channel and opens the pre-check job 48 h before a scheduled
  upgrade.

## Node pool upgrade strategy per workload class

Rule zero: one node pool at a time per cluster; one cluster at a time per wave.

| Pool | Strategy | Settings | Why |
|---|---|---|---|
| dev/stg pool-default | surge | maxSurge 2, maxUnavailable 0 | fast, cheap |
| prod pool-default-v2 (18 nodes) | surge for patches; blue-green for minors | surge: maxSurge 3, maxUnavailable 0. Blue-green: batch 25% of nodes, batch soak 10 min, node pool soak 2 h | minors are where API removals and kubelet changes bite; blue-green gives an instant rollback while the old pool exists |
| prod pool-stateful (6 x highmem-16, mdm-search) | manual, one node at a time, gated | surge maxSurge 1, maxUnavailable 0, but driven by the pipeline: cordon, drain one node, wait for search cluster green and no relocating shards, next | shard relocation takes 25-40 min; any automatic strategy that drains faster than that turns the cluster yellow/red |
| stg pool-batch | surge | maxSurge 1, maxUnavailable 0 (today 0/1 removes capacity) | |

Quota (us-central1, tsl-riq-prod): N2_CPUS limit 480, used 400, free 80. Blue-green of
pool-default-v2 needs another 18 x 8 = 144 vCPU while both pools exist, so it needs +64 at least;
request +200 (also covers the +8 nodes needed to take 100% traffic, 64 vCPU) 10 business days
before each minor wave. Surge 3 needs 24 vCPU and fits today. us-east4 has 96 free: also short for
blue-green. Cost of blue-green: 144 extra vCPU for about 3-4 hours per minor per cluster, roughly a
day of one pool per quarter; cheap compared with 34 minutes of MDM budget.

## Workload readiness requirements

Every prod workload must pass these before a cluster enters an upgrade wave; the check runs in CI
on rendered manifests and as a pre-upgrade job against live state:

- A PDB that allows at least one disruption at full replica count: `maxUnavailable: 1` (or a
  percentage) preferred over `minAvailable`. Reject `minAvailable` equal to replicas, and any PDB
  whose live `disruptionsAllowed` is 0 before the window (pre-check fails the wave).
- riq-ledger-reconciler: implement leader election and run 2 replicas (short term: PDB
  `maxUnavailable: 1` and accept a known, alerted restart of under 1 minute).
- rdm-api: add a PDB (maxUnavailable 25%).
- Readiness probes, `preStop` sleep at least as long as the load balancer deregistration, and
  `terminationGracePeriodSeconds` that fits the drain budget. riq-scoring-worker needs 600 s:
  fine for surge (GKE waits) but its PDB must not stack with a slow drain; its redelivery is safe.
- Topology spread across zones and nodes for stateless APIs (no two replicas of a 6-replica
  service on the same node).
- rdm-nightly-rebuild (02:00-05:30 UTC) is not restartable: windows are 14:00-20:00, and the job
  gets `cluster-autoscaler.kubernetes.io/safe-to-evict: "false"` plus a make-restartable ticket.
- mdm-search: masters `maxUnavailable: 1`, data `maxUnavailable: 1`, and the pipeline gates each
  node on search health (PDBs cannot see shard relocation).
- Add-ons: Crossplane providers and other CRD-heavy controllers are checked against the target
  Kubernetes version (deprecations list, provider release notes) in stg before prod.

Enforcement: the readiness check is a platform-owned policy (admission policy plus CI check), and
its report is a go/no-go input. A team that fails it blocks only its own cluster's wave after a
deadline, not the fleet.

## Fleet rollout order, gates and rollback

```text
dev-1 (auto, Regular) -> stg-1 (window) -- soak 14 d -->
  prod-green: drain traffic to blue (100%), CP upgrade, pools one by one, restore 40%, soak 3 d -->
  prod-blue:  drain traffic to green (100%), CP upgrade, pools one by one, restore 60%
```

- Before each prod cluster: scale the other region (+8 nodes, HPA max raised) and shift traffic to
  it through the multi-cluster Gateway weights, so the upgrading cluster serves 0-10% (canary
  traffic) during node drains. Shift back after pools are done and SLIs are clean for 30 minutes.
- Go/no-go before each step: readiness report clean, error budget remaining above 50% for every
  service on the cluster, no burn-rate alert in the last 24 h, no open P1/P2, quota confirmed,
  engineer on the bridge.
- Abort during a step: fast burn alert (14.4x) fires, any PDB blocks a drain more than 15 minutes,
  mdm-search not green 45 minutes after a node.
- Rollback: control plane minors cannot be downgraded, which is why the control plane only moves
  after the version soaked in stg and the other prod region. Node pools: blue-green rollback while
  the blue pool exists (within the soak); after that, create a pool on the previous version (allowed
  within skew) and move workloads with cordon/drain. Traffic stays on the healthy region meanwhile.

## Runbook

For prod-green, minor upgrade 1.33 -> 1.34 (prod-blue mirrors it):

1. T-48 h: pre-check job green (readiness report, quota, budgets). Announce in #riq, #mdm, #rdm.
2. T-0: on the bridge, primary on-call informed.
   `kubectl --context prod-green get pdb -A -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,ALLOWED:.status.disruptionsAllowed | awk '$3=="0"'` must print nothing.
3. Shift traffic: set Gateway weights green 0 / blue 100; scale blue pool-default-v2 by +8; watch
   blue p95 and error ratio for 15 minutes.
4. Control plane: `gcloud container clusters upgrade prod-green --region us-east4 --master --cluster-version 1.34.X-gke.Y`. Wait for RUNNING; run the API smoke test (Argo sync status, Crossplane providers Healthy).
5. pool-default-v2 blue-green:
   `gcloud container node-pools update pool-default-v2 --cluster prod-green --region us-east4 --enable-blue-green-upgrade --standard-rollout-policy=batch-percent=0.25,batch-soak-duration=600s --node-pool-soak-duration=7200s`
   then `gcloud container clusters upgrade prod-green --region us-east4 --node-pool pool-default-v2 --cluster-version 1.34.X-gke.Y`.
   Watch drains (`kubectl get pods -A --field-selector=status.phase=Pending`), PDB events, SLIs.
   Shift 10% traffic to green during the pool soak; if clean, let the soak finish.
6. pool-stateful: pipeline step "stateful-roll": per node cordon, drain, wait for search green and
   zero relocating shards, continue. Expect 6 x 40 min; can span two windows (pause between nodes
   is safe).
7. Restore weights 40/60, scale blue back, close the change, post the report (budget used, durations).
Abort: return weights to blue 100, `gcloud container node-pools rollback` during the blue-green
soak, stop stateful-roll, page the service owner.

## Scaling to the planned fleet

- Fleet tiers in a versions file: tier A (prod, PCI), tier B (stg, edge), tier C (dev, load test);
  each tier has a channel, window template, exclusion policy and wave position. New clusters join
  a tier, not a custom schedule. EU clusters form their own prod pair with the same blue/green
  pattern.
- A fleet upgrade pipeline (triggered by notifications and the versions file) runs pre-checks,
  traffic shifts and node pool steps; humans approve each prod cluster. The readiness policy is
  distributed through Argo CD or Config Sync to every cluster.
- 6 platform engineers: one "upgrade captain" per quarter owns the wave; service teams own their
  readiness findings with a deadline; the on-call rotation runs the runbook but is not the owner.
- Review after each wave: budget burned per cluster, time per pool, readiness findings fixed.

## Risks and open questions

- Quota requests can take a week: file them at the start of each wave.
- Leader election for riq-ledger-reconciler is application work; the RIQ team must commit to it.
- Whether PCI clusters may use Extended channel (cost) needs a decision with InfoSec.
- Autopilot for the edge clusters would remove node toil but loses pool-level control; evaluate.
