# Reference: connect/w8-c3

Model answer: `.grading/solution/DESIGN.md`. What great looks like:

- Precise about the platform: there is no contact flow alias API or CFN type (CreateContactFlowVersion is
  campaign-only); flow modules have versions and aliases (Nov 2025); native flow test cases exist
  (test designer Nov 2025, APIs Feb 2026, AWS::Connect::TestCase). Designs that invent flow aliases or
  "blue/green flow versions" lose most of the IaC and rollback points.
- Puts logic in modules so most rollbacks are alias moves; treats the exported flow JSON in git as the
  version; records previous content per release.
- Fixes the actual root cause class from w8-t1 (references) with generated manifests, a fail-closed
  promotion tool, a ref gate, and IntegrationAssociation in IaC.
- Tests that exercise the real paths (bot intents, error branches) rather than DTMF-only smoke calls.
- Ties approvals to evidence: standard changes allowed because the pipeline enforces tests and rollback.
- Gives the offshore teams real ownership of dev/test and prepared prod releases, with clear RACI.

Common weaknesses: Terraform-for-everything without noting rules/views/flow alias gaps; "manual
export/import with a checklist"; no DR plan; alarms without an automatic action.
