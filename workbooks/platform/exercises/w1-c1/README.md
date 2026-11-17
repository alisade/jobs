# platform/w1-c1 - Foundation guardrails over a Terraform plan

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 1 (Mon IAM and hierarchy, Wed Workload Identity Federation, Thu org policies); Week 3 (policy validation on the plan)

## Scenario

Tessellate Systems (fictional) is building its GCP landing zone in Terraform: an organization
(`812345678901`), `platform` and `workloads` folders, a Shared VPC host project `tsl-net-host-prod`,
service projects for MDM, RIQ and RDM, organization policies, and a Workload Identity Federation (WIF)
pool so GitHub Actions can apply without service account keys.

InfoSec signs off on the CI apply path only if every plan is checked against the foundation guardrails
before apply. Google's answer to that is `gcloud beta terraform vet`, which evaluates the **plan**, not
the HCL, so that module outputs, `for_each` expansions and defaults are all resolved. The CI runner has no
gcloud, so the platform team writes a small checker over `terraform show -json tfplan` output. Three rules
are done; you write the rest.

## What you have

| Path | What it is |
|---|---|
| `guardrails.py` | the checker: plan loading, the `Resource` wrapper, the rule registry, CLI. GR001, GR006, GR009 done |
| `policy.yaml` | the guardrail inputs: org id, GitHub owner, allowed regions, required org policies, basic roles |
| `plans/foundation.plan.json` | `terraform show -json` of the first foundation PR (31 resource changes) |
| `tests/` | visible tests |

Plan JSON shape you need: `resource_changes[]` with `address`, `mode` (`managed` or `data`), `type`, and
`change.actions` (`["create"]`, `["update"]`, `["delete"]`, `["delete","create"]`, `["no-op"]`),
`change.after` (planned values) and `change.after_unknown` (`{"attr": true}` when Terraform only knows the
value after apply). `Resource.get()` already returns the `UNKNOWN` sentinel for those.

## Your task

Implement these rules. Findings are `Finding(rule, address, severity, message)`; severity `error`
unless stated.

| Rule | Check |
|---|---|
| GR002 | No basic roles (`policy.basic_roles`) on `google_{organization,folder,project}_iam_{member,binding}`. Unknown role: warning. |
| GR003 | No `user:` principals on organization or folder IAM (members or bindings). Project level is out of scope. |
| GR004 | A `google_iam_workload_identity_pool_provider` whose OIDC issuer is `https://token.actions.githubusercontent.com` must have an `attribute_condition` that pins the GitHub org: `assertion.repository_owner == '<github_owner>'`, or `assertion.repository_owner_id == '<digits>'`, or `assertion.repository == '<github_owner>/<repo>'`. A condition containing `\|\|` is rejected (it can bypass the pin). Missing or empty condition: error. Unknown condition: warning. Other issuers: ignore. |
| GR005 | At the **organization** (`parent == organizations/<org_id>`; folder or project policies do not count), `google_org_policy_policy` must exist for every `required_org_policies.boolean` constraint with a rule `enforce: "TRUE"`, every `deny_all` constraint with a rule `deny_all: "TRUE"`, and the `locations` constraint with `values[].allowed_values` all inside `allowed_regions` (`in:<region>-locations`, `<region>` or `zones:<region>`; `allow_all` is a violation). A missing constraint is reported once per constraint at address `organizations/<org_id> (org policies)`. |
| GR007 | `google_storage_bucket`: `uniform_bucket_level_access` true, `public_access_prevention` `"enforced"`, `location` (case-insensitive) in `allowed_regions` or `extra_bucket_locations`. |
| GR008 | Every `google_compute_shared_vpc_service_project` attaches to a project that has a `google_compute_shared_vpc_host_project` in the plan; every `google_project` labelled `network = "shared"` is attached. Unknown host or service project: warning. |

General rules: skip `["delete"]` changes and `mode: data`; never crash on `UNKNOWN`; results sorted and
de-duplicated (already done in `evaluate`). Keep the CLI contract: `--json` prints an array of findings;
exit 0 with no errors, 1 with at least one error, 2 for unreadable input.

## Acceptance criteria (what the grader checks)

- On `plans/foundation.plan.json` the error findings are exactly the twelve (rule, address) pairs the
  rules above imply. Read the plan; do not hard-code them.
- Each rule's edge cases: deletes, data sources, bindings vs members, folder vs org policy parents, the
  WIF condition variants, case-insensitive bucket locations, unknown values as warnings.
- CLI exit codes and JSON shape.
- `ANSWER.md`: your design decisions and the AWS mapping for each rule (SCP, IAM OIDC provider for GitHub,
  account-level S3 Block Public Access, and so on).

## How to run

```bash
make setup
make run                       # findings for the foundation plan
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade platform/w1-c1
make clean
```

If you have Terraform installed you can produce your own plan JSON later (`terraform plan -out tfplan &&
terraform show -json tfplan > plan.json`) and run the checker on it. The grader never needs Terraform.

## What to submit

`guardrails.py` and `ANSWER.md`.
