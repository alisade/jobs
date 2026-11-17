# ANSWER: platform/w3-t1

## Approach

`make plan`, then compared generated.tf with the cleaned config and the PR diff.

## Root cause

The plan shows `-/+ auto_create_subnetworks = false -> true # forces replacement` on
google_compute_network.riq_legacy. generated.tf had `auto_create_subnetworks = false`; PR #418 removed it
("anything that is false ... goes"). The provider default is true and the attribute is ForceNew, so the
config describes an auto-mode VPC and Terraform plans to destroy and recreate the network that carries
the RIQ GKE nodes and Postgres. The bucket label diff is the same cleanup dropping `env = "prod"`:
in-place and harmless, not the danger.

## Fix

Restored the attribute and the label; added prevent_destroy to the network and the SQL instance. Plan: 5
to import, 0 to add, 0 to change, 0 to destroy. A hand-made ForceNew drift now errors.

## Trade-offs / what I would do in production

Cleanup by schema (keep ForceNew attributes and non-default values), CI gate for imports-only migration
plans, prevent_destroy on stateful resources, small batches.
