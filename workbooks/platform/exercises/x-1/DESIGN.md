# Design: zero-downtime maintenance strategy for the Tessellate GKE fleet

<!-- Audience: Dana K. (platform lead), service owners of RIQ, MDM, RDM, and the on-call rotation.
4-8 pages equivalent. Use inputs/. Be specific: GKE settings, numbers, commands, owners.
Diagrams in ```text or ```mermaid. -->

## Context, goals and non-goals

<!-- What "zero downtime" means here in SLO terms, what failed in INC-3982, scope (control plane,
nodes, add-ons, the 10 planned clusters), what is out of scope. -->

## Version and channel strategy

<!-- Release channel per environment and why; how a version flows dev -> stg -> prod-blue ->
prod-green; skew policy limits and the current prod-blue skew; who decides and when. -->

## Maintenance windows and exclusions

<!-- Windows per cluster tied to the staffed calendar; which exclusion scope for each freeze and its
limits; how you avoid GKE upgrading at the worst time; how notifications drive automation. -->

## Node pool upgrade strategy per workload class

<!-- Surge vs blue-green vs autoscaled blue-green per pool, with settings (maxSurge/maxUnavailable,
batch size, soak). Quota and cost of each. Dedicated pools where needed. -->

## Workload readiness requirements

<!-- What every service must have before a fleet upgrade: PDBs that allow disruptions, probes,
grace periods, preStop, topology spread, the singleton and stateful cases, the CronJob. How you
check this automatically. -->

## Fleet rollout order, gates and rollback

<!-- Waves, soak times, go/no-go checks (SLO burn, error budget left, app health), traffic shifting
between prod-blue and prod-green during their upgrades, rollback options for control plane and
node pools. -->

## Runbook

<!-- Step by step for one prod cluster: pre-checks, commands (gcloud / kubectl), what to watch,
abort criteria, communication. -->

## Scaling to the planned fleet

<!-- How this works for 14 clusters and 15 teams with 6 platform engineers: automation, fleet
features, policy, ownership. -->

## Risks and open questions

<!-- What could still go wrong, and decisions you need from others. -->
