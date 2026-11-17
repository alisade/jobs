# ANSWER: platform/w1-c1 Foundation guardrails over a Terraform plan

## Approach

I evaluate `change.after` for every managed resource change except pure deletes, because that is what
will exist after apply, with module expansions and defaults resolved. Values in `after_unknown` become
warnings so a computed value can never slip past a rule. Per-resource rules are registered with a
decorator; the two rules that need the whole plan (required org policies, Shared VPC attachments) run
once over the resource list.

## Fix

- GR002/GR003: one IAM type table drives both rules; `_member` and `_binding` handled by `iam_members()`.
- GR004: accepted pins are repository_owner, repository_owner_id or an owner-prefixed repository; any
  `||` is rejected because it can widen the condition.
- GR005: org policies indexed by constraint for the org parent only; boolean, deny_all and location
  shapes checked separately; a missing constraint is reported at the org address.
- GR007/GR008: bucket controls and Shared VPC attachment, unknowns as warnings.

## Trade-offs / what I would do in production

Runs as a required CI check between plan and apply, alongside `gcloud beta terraform vet` or conftest.
AWS mapping: SCP deny on access keys vs `iam.disableServiceAccountKeyCreation`; GitHub OIDC trust policy
`sub` condition vs WIF `attribute_condition`; S3 Block Public Access vs public access prevention; OUs
vs folders. Limits: it cannot see IAM granted outside Terraform or inherited from above the org root, so
I would pair it with a Cloud Asset Inventory IAM export and add deny policies and VPC-SC dry-run checks
next.
