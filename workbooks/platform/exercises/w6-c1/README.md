# platform/w6-c1 - plan-gate: a Terraform plan JSON gate for CI

**Type:** coding (Go) | **Estimate:** 2-3 hours | **Study plan:** Week 6 (Go for platform tooling); Week 3 (policy against the plan, imports)

## Scenario

Tessellate is bringing the hand-built resources of `tsl-riq-prod` and friends under Terraform in
small import batches. Import batch 07 looked fine in review ("just imports") until Marco D. scrolled
to the bottom of a 900-line plan and found `-/+ google_compute_network.riq_core`: the cleaned-up
generated config had dropped an attribute that forces replacement.

Dana K. wants a gate that does not depend on someone scrolling: a small Go binary that runs in every
Terraform pipeline after `terraform plan -out plan.out && terraform show -json plan.out > plan.json`,
and in the import agent's verification step. It reads the plan JSON (the plan, not the code, is what
will be applied), prints a terraform-style summary, enforces a policy and exits with a code CI can use.

## What you have

| Path | What it is |
|---|---|
| `gate/types.go` | plan JSON types, `Policy`, `Summary`, `AttrChange`, `Violation`, loaders (do not change) |
| `gate/classify.go` | `Classify`, `Validate`, `Summarize` - TODO (`SummaryLine` is done) |
| `gate/diff.go` | `ChangedAttributes` with sensitive masking - TODO |
| `gate/policy.go` | `Evaluate` - TODO |
| `gate/run.go` | `Run` (CLI) and `Build` - TODO (`WriteText` is done) |
| `cmd/plan-gate/main.go` | the binary |
| `testdata/*.plan.json` | realistic `terraform show -json` output: import batch 07 (clean), batch 07 with the VPC replace, an ordinary app change PR |
| `testdata/policy-*.json` | the migration policy (imports only) and the default policy |
| `gate/gate_test.go` | visible tests |

## Your task

1. `Classify`: `["no-op"]`, `["create"]`, `["read"]`, `["update"]`, `["delete"]`; both
   `["delete","create"]` (destroy first) and `["create","delete"]` (create_before_destroy) are a
   replace; anything else is an error.
2. `Validate`: `format_version` must exist with major version 1 (a state file or a future format is
   not a plan you understand); every action set must classify.
3. `Summarize`: count like the last line of `terraform plan`: imports from `change.importing`
   (independent of the action), a replacement counts once in add and once in destroy (and in
   `Replace`); data sources (`mode: data`) are not counted.
4. `ChangedAttributes`: top-level attributes that differ between `before` and `after`, sorted, values
   as compact JSON or `null`; mask with `(sensitive value)` when `before_sensitive`/`after_sensitive`
   is `true` for that attribute or contains `true` anywhere below it.
5. `Evaluate`: `protected_type` (delete or replace of a protected type, in any mode),
   `imports_only_action` (any create, delete or replace when `imports_only` is set) and
   `imports_only_attribute` (an update touching an attribute outside `allowed_update_attributes`, one
   violation per attribute). Include `action_reason` in the message when present. Sort by address,
   then rule. Data sources never violate.
6. `Run` and `Build`: `-plan` (required), `-policy` (optional), `-json`. Exit `0` pass, `1` any
   violation, `2` usage, read, decode or validation error (message on stderr, nothing claiming PASS).
   The JSON report has `summary`, `changes` (sorted by address; skip no-op and read unless importing;
   include `changed_attributes` for update and replace, `replace_paths` joined with `.`),
   `violations` (an empty array, never null) and `result`.

Try it: `make run PLAN=testdata/import-batch-07-replace.plan.json POLICY=testdata/policy-migration.json`.

## Acceptance criteria

- `make test` passes; hidden tests cover both replace orders, data sources, protected and
  imports-only rules, nested sensitive masking, the JSON and text reports, and every exit-2 path.
- No sensitive value from the fixtures appears in any output.
- `ANSWER.md`: why the gate evaluates the plan JSON rather than HCL, where it sits in the pipeline
  (and why it must run on the same plan file that apply uses), and what it cannot catch.

## How to run

```bash
make setup
make test
make run PLAN=testdata/app-change.plan.json ARGS=-json
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade platform/w6-c1
make clean
```

## What to submit

`gate/classify.go`, `gate/diff.go`, `gate/policy.go`, `gate/run.go` and `ANSWER.md`.
