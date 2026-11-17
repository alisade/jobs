# Reference: platform/w4-t1

Root cause: the composed resources reference `providerConfigRef: {name: default}` with no kind. In this
Crossplane v2 model (namespaced MRs), the kind defaults to `ProviderConfig`, which is namespaced and
resolved in the MR's namespace. The platform installs only `ClusterProviderConfig/default`. Describe
shows `Kind: ProviderConfig` and "cannot get referenced ProviderConfig ... not found"; `get
providerconfigs -A` is empty while `clusterproviderconfigs` has default. The token warning was transient
(refreshed four seconds later) and keys are against policy.

Fix: `.grading/solution/platform/composition.yaml` sets `providerConfigRef: {kind: ClusterProviderConfig,
name: default}` on every base. A new team namespace then works with no extra objects. Per-team
ProviderConfigs (each with its own Google service account via Workload Identity) are a valid tenancy design, but they should
be created by the namespace onboarding, not as a hand-made workaround.

Prevention: render and composition tests in CI with sample XRs per namespace, alerts on Synced=False
MRs, staged composition revisions.
