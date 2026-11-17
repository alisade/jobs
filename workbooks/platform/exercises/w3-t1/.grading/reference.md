# Reference: platform/w3-t1

Root cause: `-generate-config-out` wrote `auto_create_subnetworks = false` (generated.tf). PR #418's
cleanup rule ("anything false, null or equal to a default goes") deleted it. For
`google_compute_network` the provider default is `true` and the attribute forces replacement, so the
config now describes an auto-mode VPC while live is custom mode: `-/+ auto_create_subnetworks = false ->
true # forces replacement`. Apply would destroy riq-legacy and create an auto-mode VPC; with real
Terraform the subnets referencing the network and everything attached (GKE nodes, the Postgres private
IP) would follow.

Red herring: the bucket label diff is the same cleanup dropping `env = "prod"`; it is an in-place update
and harmless, but a migration batch must be imports only, so restore it in config.

Fix: `.grading/solution/migration/`: restore `auto_create_subnetworks = false` and the label, add
`lifecycle { prevent_destroy = true }` to the network and the SQL instance. Plan: 5 to import, 0/0/0.

Prevention: cleanup rule based on the provider schema (keep ForceNew attributes and values that differ
from the default), a CI gate that fails non-import migration plans, prevent_destroy on stateful
resources, small batches.
