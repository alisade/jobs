# platform/w2-t1 - prod-blue node pool upgrade stuck at 1 of 6 nodes

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 2 (Wed surge vs blue-green and quota, Thu PDBs and draining)

## Scenario

Tessellate (fictional) upgrades `prod-blue` (GKE Standard, Stable channel) in its Wednesday 03:00 UTC
maintenance window. The `default` node pool uses surge upgrades (`maxSurge: 1`, `maxUnavailable: 0`).
One node upgraded, the second has been draining for almost an hour and the upgrade watchdog paged.
GKE only honours PodDisruptionBudgets for a bounded time during a node drain before it evicts anyway, so
the clock is running. ArgoCD syncs the rendered manifests in `k8s/` to the cluster.

## What you have

| Path | What it is |
|---|---|
| `evidence/PAGE.txt` | the page and the on-call thread |
| `evidence/gke-operation.txt` | the GKE operation, node pool upgrade settings, node pool logs |
| `evidence/kubectl.txt` | PDBs, RIQ pods, PDB status, events, canary logs |
| `k8s/` | rendered manifests ArgoCD applies (`riq/canary.yaml` belongs to the RIQ team: you may not change that chart) |
| `cluster/state.json` | nodes in upgrade order and the pods on them, as captured at 04:50 |
| `tools/drain_sim.py` | a drain simulator that applies the Eviction API's PDB arithmetic (read the docstring) |

## Your task

1. `make drain` and the evidence: which pod cannot be evicted, and which budget blocks it?
2. Explain why that budget allows zero disruptions although all four stable pods are Ready. Show the
   arithmetic (expected, desiredHealthy, currentHealthy).
3. Decide whether the quota warning matters.
4. Fix it in `k8s/` so the drain completes, without deleting or neutering the budget. The RIQ team keeps
   shipping canaries as a Deployment `riq-api-canary` with pod labels `app: riq-api, track: canary`.
5. `ANSWER.md`: root cause and evidence, the immediate mitigation you would do in the next five minutes
   (and what you would not do), the permanent fix and how you would prevent a repeat.

## Acceptance criteria (what the grader checks)

- With your manifests every node drains, whether the canary is crash-looping, healthy, or not deployed.
- The `riq/riq-api` budget selects exactly the four stable pods (expected 4, one disruption allowed), and
  still blocks a drain when two stable pods are not Ready.
- The stable Deployment (4 replicas, readiness probe) and the mdm budgets are unchanged.
- `ANSWER.md` explains the cause with evidence and rules out the red herring.

## How to run

```bash
make setup
make drain     # simulate the drain against k8s/
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade platform/w2-t1
make clean
```

## What to submit

Your changes in `k8s/` and `ANSWER.md`.
