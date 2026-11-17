# Postmortem summary: INC-3982, 2026-07-19, prod-blue node upgrade (blameless)

- Saturday 07:10 UTC GKE started an automatic node upgrade of prod-blue pool-default-v2 and
  pool-stateful inside the Sat-Sun window, 1.31 to 1.32, both pools in parallel, surge 1/0.
- 07:42 two mdm-search data pods were evicted within 20 minutes (one per pool drain wave), the search
  cluster went red for 11 minutes, MDM API p95 3.2 s, 34 minutes of MDM error budget burned.
- 08:15 riq-ledger-reconciler drain blocked (PDB minAvailable 1 on 1 replica); after about an hour
  GKE stopped waiting for the PDB and evicted the pod; reconciler down 6 minutes, ledger lag alert.
- 09:30 rdm-nightly-rebuild was unaffected only because it had finished at 05:20.
- Nobody was on the bridge: the window was chosen as "low traffic", not "staffed". Primary on-call
  was paged at 07:44 and had never run a GKE upgrade.
- prod-green was upgraded by GKE the following weekend with the same result for mdm-search (shorter,
  6 minutes red). Nothing gated green on blue's outcome.
- Action items left open: "decide a fleet upgrade strategy", "fix singleton PDBs", "upgrade runbook".

Today (2026-11-12) prod-blue nodes are still on 1.32 under a 1.33 control plane; prod-green is fully
on 1.33. Stable channel will offer 1.34 in the coming weeks.
