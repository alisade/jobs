# platform/x-1 - Zero-downtime maintenance strategy for the Tessellate GKE fleet

**Type:** design (optional, add-on week; review-only, graded by rubric) | **Estimate:** 2-3 hours | **Study plan:** Week 2 (GKE fleet operations); add-on week 7

## Scenario

"Design zero downtime maintenance strategies for fleets of kubernetes clusters" is the most concrete
duty in the posting, and Tessellate needs one now. INC-3982 (July) showed every failure mode at once:
GKE upgraded prod-blue's two node pools in parallel inside a "low traffic" window that nobody
staffed, a stateful search cluster lost two data pods within twenty minutes, a singleton's PDB
blocked the drain until GKE stopped waiting, and prod-green repeated it a week later because nothing
gated green on blue. The action items ("decide a fleet upgrade strategy", "fix singleton PDBs",
"upgrade runbook") are still open. Stable will offer 1.34 soon, prod-blue nodes are still one minor
behind their control plane, and ten more clusters arrive in 2027.

Dana K. asks you, as the staff engineer, for the strategy and the runbook.

## What you have

| Path | What it is |
|---|---|
| `inputs/fleet-inventory.yaml` | clusters, channels, versions, windows, node pools, traffic split, 2027 plans |
| `inputs/quotas.txt` | regional quotas and usage for the prod project |
| `inputs/workloads.md` | workload classes with PDBs, grace periods and quirks |
| `inputs/calendar-and-slos.md` | freezes, staffed change windows, SLOs and error budgets, on-call shape |
| `inputs/incident-2026-07-19-upgrade.md` | the INC-3982 postmortem summary |
| `DESIGN.md` | the template you fill in |

## Your task

Fill in every section of `DESIGN.md` and the `ANSWER.md` template. Be specific to GKE and to these
inputs: name settings (release channel, maintenance window and exclusion scopes, `maxSurge` /
`maxUnavailable`, blue-green batch and soak settings), show the quota arithmetic, give commands in
the runbook, and say who decides what. Check current limits (for example on maintenance exclusions
and window availability) in the GKE docs linked from the study plan rather than from memory.

## Acceptance criteria (what the rubric looks for)

- Channels and version flow per environment, with the skew policy and the prod-blue skew handled.
- Windows aligned with staffed hours; exclusion scopes for each freeze within their documented limits.
- A strategy per workload class (stateless, workers, long jobs, stateful search, singleton, add-ons),
  with quota and cost for blue-green computed from `inputs/quotas.txt`.
- Workload readiness rules and how they are enforced (policy check in CI or admission, not a wiki).
- Fleet waves with soak, go/no-go gates on SLO burn and error budget, traffic shifting between the
  two prod regions, and rollback for both control plane and node pools.
- A runbook someone else on the 12-hour rotation could execute.
- How it scales to 14 clusters with 6 platform engineers.

## How to run

```bash
make setup      # nothing to install; read inputs/
# write DESIGN.md and ANSWER.md
make test       # completeness report (rubric-graded, no tests)
# from workbooks/ in Claude Code: /grade platform/x-1
make clean
```

## What to submit

`DESIGN.md` and `ANSWER.md`.
