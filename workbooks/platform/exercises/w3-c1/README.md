# platform/w3-c1 - Import blocks from a Cloud Asset Inventory export

**Type:** coding | **Estimate:** 2-2.5 hours | **Study plan:** Week 3 (import blocks, Cloud Asset Inventory, bulk export); Week 6 (the unmanaged-resource agent uses this as a tool)

## Scenario

Tessellate (fictional) is bringing hand-built GCP resources under Terraform, one project at a time.
Writing import blocks by hand is the toil: each resource type has its own import ID format, the default
network and Google-managed identities must not be imported, and resources already in state must be
skipped. `gcloud beta resource-config bulk-export` covers part of this but not your conventions, so the
platform team writes a small generator over a Cloud Asset Inventory export. Its output is the input to
`terraform plan -generate-config-out`, which drafts the resource config.

## What you have

| Path | What it is |
|---|---|
| `importgen.py` | the generator: loaders, rendering, CLI; Network and Firewall mapped |
| `inventory/cai-export.json` | a CAI export of `tsl-riq-prod` (resources plus the project IAM policy) |
| `inventory/state-ids.json` | import IDs Terraform already manages (address -> ID) |
| `inventory/projects.json` | project number -> project ID |

## Your task

**Mappings** (`map_asset`), with the google provider's import ID formats:

| Asset type | Resource | Import ID |
|---|---|---|
| compute.googleapis.com/Network | google_compute_network | `projects/{project}/global/networks/{name}` |
| compute.googleapis.com/Subnetwork | google_compute_subnetwork | `projects/{project}/regions/{region}/subnetworks/{name}` |
| compute.googleapis.com/Firewall | google_compute_firewall | `projects/{project}/global/firewalls/{name}` |
| storage.googleapis.com/Bucket | google_storage_bucket | `{project}/{name}` (project from the asset's parent project number) |
| iam.googleapis.com/ServiceAccount | google_service_account | `projects/{project}/serviceAccounts/{email}` |
| sqladmin.googleapis.com/Instance | google_sql_database_instance | `projects/{project}/instances/{name}` |
| project IAM policy bindings | google_project_iam_member | `{project} {role} {member}` (space separated), one per member |

Anything else goes to the report as unsupported.

**Skip rules** (to the report as skipped): the network named `default`; Google-managed service accounts
(`*@developer.gserviceaccount.com`, `*@cloudservices.gserviceaccount.com`, `*@appspot.gserviceaccount.com`,
and service agents `service-<number>@...`), both as service account assets and as IAM members; any binding
whose role ends with `serviceAgent`. IDs already in `state-ids.json` are not emitted and are listed as
already managed.

**Grouping and identifiers**: one file per owner, `imports/<owner>/imports.tf`, from the `owner` label
(`labels`, or `settings.userLabels` for Cloud SQL), lowercased with anything outside `[a-z0-9-]` turned
into `-`; no owner means `platform`. Subnetworks take their network's owner. Identifiers: lowercase,
anything outside `[a-z0-9_]` becomes `_`, runs of `_` collapse, leading and trailing `_` are stripped, a
leading digit gets an `r_` prefix. Base names: the resource name, the service account id (before `@`),
and for IAM members `<role after roles/>_<member before @>`. Collisions within one file and type get
`_2`, `_3`, in import ID order.

**Output**: blocks sorted by type then identifier, the header comment, byte-identical for the same input
in any order. The CLI writes the files and `imports/report.json`.

## Acceptance criteria (what the grader checks)

- Exactly the expected 13 blocks, each in the right file with the right ID.
- The report: the default network, the default compute SA, the two Google-managed bindings skipped; the
  Pub/Sub topic unsupported; the two state IDs already managed.
- Identifier rules and collision suffixes; shuffled input gives identical files; the CLI works.
- `ANSWER.md`: design notes and how this fits a migration method.

## How to run

```bash
make setup
make run
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade platform/w3-c1
make clean
```

## What to submit

`importgen.py` and `ANSWER.md`.
