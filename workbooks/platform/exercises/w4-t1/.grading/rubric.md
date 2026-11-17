# Rubric: platform/w4-t1 AppDatabase XRs never become Ready
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: the Composition's bases set `providerConfigRef: {name: default}` without a kind; for namespaced (v2) MRs the kind defaults to the namespaced `ProviderConfig`, looked up in the MR's own namespace (team-riq, team-mdm), but the platform only installed a cluster-scoped `ClusterProviderConfig` named default. Every MR fails to connect, so the XR stays unready. Partial (10-15): "provider config not found" without kind vs scope. Zero: Workload Identity or tokens. |
| 3 | Evidence | 20 | Full: describe output (Kind ProviderConfig, the ReconcileError), `get providerconfigs -A` empty vs `clusterproviderconfigs` default, trace output, simulator output. Partial: one or two. |
| 4 | Red herring handled | 5 | Token warning was transient and refreshed 4 seconds later; a key secret would also violate the no-keys policy and would not fix the lookup. |
| 5 | Fix quality | 10 | `kind: ClusterProviderConfig` in each composed resource base (or a patch), mappings untouched, no per-namespace objects needed; discusses per-team ProviderConfig as a deliberate tenancy choice rather than a workaround. |
| 6 | Prevention | 10 | `crossplane render` or composition tests in CI against sample XRs, an alert on MRs with Synced=False for N minutes, staged composition revisions, release notes for v1 to v2 migrations. |
Total: 100
