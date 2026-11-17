# ANSWER: connect/w8-c3 CI/CD and release management for Connect

## Approach

Started from the pain points and the 2026-10-06 incident, then mapped every resource to what
CloudFormation/CDK actually supports, because that decides where versioning and rollback can come from.

## Fix

- Flows as exported JSON in git, promoted by the logical-name promotion tool with check-refs; no flow
  alias API exists, so the release record of previous content is the rollback.
- Shared logic in flow modules with versions and aliases; Lambdas and Lex with aliases; rollback is
  mostly an alias move.
- Everything else (queues, profiles, associations, rules, evaluation forms, prompts, test cases) in CDK,
  with manifests generated from stack outputs.
- One GitHub Actions pipeline with OIDC per account, environments with required reviewers, native flow
  test cases and synthetic calls as gates, 30-minute alarm watch with automatic rollback, DR in the same run.
- Standard-change approval for gated flow releases; offshore teams own dev/test releases.

## Trade-offs / what I would do in production

Not putting flows in CloudFormation yet (console-first team, churn); revisit once modules carry most
logic. First spike: native test cases for the bot path and their run time in CI. Risk: auto-rollback
trusts thin tests; grow coverage from incidents.
