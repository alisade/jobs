# Reference: platform/w1-c1 Foundation guardrails over a Terraform plan

The reference implementation is `.grading/solution/guardrails.py`. Key points:

- **Evaluate the plan, not the code.** `resources()` yields only managed resources whose change has an
  `after` and is not a pure delete. Replacements (`["delete","create"]`) are evaluated on their `after`.
- **Unknown values.** `Resource.get()` returns `UNKNOWN` when `after_unknown[attr]` is true. Every rule
  that needs a value turns `UNKNOWN` into a `warning` with a "re-check after apply" message. A guardrail
  that silently passes unknowns is a bypass: put the risky value behind a computed expression and the
  check never sees it.
- **Cross-resource rules** (GR005, GR008) run once over the full resource list, because "constraint X is
  missing" and "project P is not attached" are facts about the plan, not about one resource.
- **GR004.** Accepts `assertion.repository_owner == 'tessellate'`, `assertion.repository_owner_id ==
  '<digits>'` or `assertion.repository == 'tessellate/<repo>'`, rejects any condition with `||`. The
  owner-id form is the strongest because org names can be re-registered after deletion.
- **GR005.** Indexes org policies by constraint name for `parent == organizations/<id>` only. Boolean
  constraints need `enforce: "TRUE"`, list constraints that must block everything need `deny_all: "TRUE"`,
  `gcp.resourceLocations` needs `allowed_values` inside the allowed regions (`in:us-east4-locations`).

Expected errors on the fixture (12): GR001 legacy_ci key; GR002 riq-devs roles/editor; GR003
dana.k on the workloads folder; GR004 github_legacy provider with no condition; GR005
gcp.resourceLocations allows europe-west1, uniformBucketLevelAccess not enforced, and
compute.skipDefaultNetworkCreation missing; GR006 core-euw1 region and core-usc1-gke without Private
Google Access; GR007 riq_exports (location EU, not uniform, not enforced); GR008 and GR009 on the RDM
project (labelled shared but not attached, and auto_create_network true).

AWS mapping a strong ANSWER.md gives:

| Rule | AWS habit | GCP control |
|---|---|---|
| GR001 | SCP deny `iam:CreateAccessKey`, IAM roles instead of users | `iam.disableServiceAccountKeyCreation`, WIF and impersonation |
| GR002 | no `AdministratorAccess` to humans | no basic roles; predefined or custom roles |
| GR003 | Identity Center groups, not IAM users | groups from Cloud Identity bound at folder or org |
| GR004 | IAM OIDC provider trust policy with `token.actions.githubusercontent.com:sub` condition | WIF provider `attribute_condition` plus a narrow principalSet binding |
| GR005 | SCPs on the root/OUs | org policy constraints (they restrict configuration, not API actions) |
| GR006/GR007 | region deny SCP, S3 Block Public Access | `gcp.resourceLocations`, public access prevention, uniform bucket-level access |
| GR008 | shared VPC via RAM subnet sharing | Shared VPC host and service projects |
| GR009 | delete the default VPC | `compute.skipDefaultNetworkCreation`, `auto_create_network = false` |

Production notes: run it as a required check after `terraform plan` and before apply; keep it next to
`gcloud beta terraform vet` or conftest rather than replacing them; the checker cannot see IAM granted
outside Terraform or inherited from above, so pair it with Cloud Asset Inventory and an IAM recommender
review.
