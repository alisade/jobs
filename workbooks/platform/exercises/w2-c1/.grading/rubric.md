# Rubric: platform/w2-c1 Fleet upgrade planner
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | GKE semantics | 15 | Full: one minor per control plane hop, pools never newer than the control plane, skew checked before each hop, exclusion scopes exactly as GKE documents them (patch vs minor, node vs control plane), quota per strategy. Partial: one wrong. Zero: copies versions without hops or treats every scope the same. |
| 3 | Code quality | 10 | Full: small pure functions, datetime arithmetic in UTC, reasons that an on-call engineer can act on, no hard-coded cluster names. Partial: works but tangled. Zero: special-cases the fixture. |
| 4 | ANSWER.md and production judgement | 25 | Full: explains the plan-then-apply idea for upgrades; compares with GKE's own tools (release channels, rollout sequencing for fleets, maintenance exclusions) and says when a custom planner is still worth it; go/no-go between waves (SLO burn rate, error budget, canary health), Pub/Sub cluster notifications to trigger it, approvals for prod, and what to do with prod-green (quota increase or switch to surge with a reasoned max_surge). Partial: generic. Zero: empty. |
Total: 100
