# Rubric: platform/w4-c1 AppDatabase composition function and readiness
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Reconcile semantics | 15 | Full: diff by key, apply only on difference, prune only this XR's resources in this namespace, Ready computed from observed state (not from "I just applied it"), errors wrapped with %w and returned. Partial: works but re-applies everything or computes Ready from desired. Zero: no pruning or panics. |
| 3 | Go structure and readability | 10 | Full: validation separated from building, small helpers, early returns, no global mutable state, maps for size/version lookups. Partial: one long function. Zero: copy-paste per resource with drift between them. |
| 4 | Crossplane v2 judgement in ANSWER.md | 15 | Full: namespaced XR with no claim and why; ClusterProviderConfig default vs a team ProviderConfig (blast radius, separate GCP service accounts via Workload Identity); Delete vs Orphan for prod data with a concrete recommendation (Orphan or deletion protection for prod, backups). Partial: generic. Zero: empty. |
| 5 | Production follow-ups | 10 | Concrete: composition versioning (revisions, compositionUpdatePolicy), testing with crossplane render in CI, an XRD schema with enums so bad input never reaches the function, connection secret handling (External Secrets / Secret Manager), quotas and cost guard rails per team. |
Total: 100
