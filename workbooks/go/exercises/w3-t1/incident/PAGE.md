# PagerDuty: [P2] tenant-operator Deployment unavailable (tenant-system, analytics-prod-use1)

Triggered 2026-10-06 09:31 UTC by alert `KubeDeploymentReplicasMismatch`, routed to platform-oncall.

> #analytics-platform, 09:40 UTC, from Priya (Retention ML team):
> "We created the `churn-model` Tenant in team-retention at 09:15 for today's training run.
> It has been 25 minutes, no ResourceQuota, no storage Secret, and `kubectl get tenant` shows
> READY blank. Pods for the training Job are stuck because the Job's init container reads the
> storage Secret. Tenants created last week are fine. Did something change this morning?"

Context from the on-call handover:

- ArgoCD synced `tenant-operator` v0.4.0 to analytics-prod-use1 at 09:11 UTC (auto-sync from
  `main`). The same version has been on analytics-dev-use1 since Friday; the dev on-call says
  "it works in dev". (In dev, the operator runs with the namespace's default SA bound to a
  broad `platform-dev-admin` ClusterRole; prod uses the generated `manager-role`.)
- v0.4.0 also shipped the egress NetworkPolicy from the CKS hardening ticket SEC-2290.
- The operator's CI runs envtest; it passed.

Everything collected so far is in this folder.
