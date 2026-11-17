# ANSWER: platform/w4-t1

## Approach

`make reconcile`, then the describe output and the config listings.

## Root cause

The Composition bases set `providerConfigRef: {name: default}` without a kind. Namespaced MRs default
the kind to the namespaced ProviderConfig and look it up in their own namespace (describe: "Kind:
ProviderConfig", "cannot get referenced ProviderConfig ... not found"). Only ClusterProviderConfig/default
exists (`get providerconfigs -A`: none). The token warning refreshed at 14:02:14 and is unrelated.

## Fix

`kind: ClusterProviderConfig` on every composed base. Simulator: all XRs Ready, including a new
team-rdm namespace; mappings unchanged; still Workload Identity.

## Trade-offs / what I would do in production

Per-team ProviderConfigs with separate Google service accounts only as a deliberate tenancy model created at onboarding.
Composition render tests in CI per namespace, alert on Synced=False MRs, staged composition revisions.
