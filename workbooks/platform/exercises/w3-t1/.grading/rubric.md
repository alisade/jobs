# Rubric: platform/w3-t1 Import batch 07 plans to replace the core VPC
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: the cleanup in PR #418 removed `auto_create_subnetworks = false` as "a default", but the provider default is true and the attribute forces replacement; live is a custom-mode VPC (false), so the plan replaces the network. On apply Terraform would destroy riq-legacy (and in a real plan the subnets, the GKE nodes and the Postgres private IP depending on it would be disrupted), then create an auto-mode VPC. Partial (10-15): "network is replaced" without the default/ForceNew mechanism. Zero: blames the bucket label or live drift. |
| 3 | Evidence | 20 | Full: plan line `auto_create_subnetworks = false -> true # forces replacement`, generated.tf having `= false`, the PR diff removing it with "anything false goes", the summary line. Partial: one or two. |
| 4 | Red herring handled | 5 | The label diff is the cleanup dropping `env = "prod"`; restore it in config (it is an in-place update, harmless but not import-only), do not relabel the live bucket. |
| 5 | Fix quality | 10 | Attribute restored explicitly, label restored, `prevent_destroy` on the network and the SQL instance, import IDs untouched. |
| 6 | Prevention | 10 | Cleanup rule: keep attributes that differ from the provider default or are ForceNew, diff generated vs cleaned against the schema; CI gate rejecting migration plans that are not imports only (w6-c1 style); prevent_destroy policy for stateful resources; batch sizing. |
Total: 100
