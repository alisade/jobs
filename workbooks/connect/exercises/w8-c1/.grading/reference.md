# Reference: connect/w8-c1

Reference implementation: `.grading/solution/src/promote.ts`.

Design:
- Build three indexes from the dev inventory: exact ARN -> mapping, Lambda base ARN -> mapping
  (qualifier re-appended after mapping), bare id -> mapping; plus the instance ARN and id.
  Each mapping resolves via `<kind>:<logical name>` in the target manifest.
- Walk the parsed Content recursively (objects, arrays, strings) keeping a JSONPath. In each
  string, replace ARN tokens found by regex (handles ARNs embedded in JSON-in-a-string), then
  UUID tokens that are dev resource ids and not part of an untouched ARN.
- Problems: dev-owned ARN not in inventory -> unknown-reference; mapped resource missing in
  target -> unmapped-in-target; after rewriting, any dev account/instance/resource id left ->
  dangling. Foreign-account ARNs pass through.
- Modules sorted first, then flows; artifacts carry target id/ARN; nothing emitted when any
  problem exists.

Interview points:
- Regular contact flows have no alias API (CreateContactFlowVersion is campaign-only); flow
  modules have versions and aliases (Nov 2025), so shared logic in modules can be pinned per
  environment while flows are redeployed by content. Rollback = redeploy the previous artifact.
- Generate manifests from IaC outputs (CloudFormation exports / CDK outputs / Terraform state)
  or List* APIs; hand-maintained manifests drift.
- Gate the deploy with validateFlow-style lint, native flow test cases (`AWS::Connect::TestCase`,
  `StartTestCaseExecution`) and a synthetic test call; alarm on `ContactFlowErrors` after release.
- Lex: the target bot alias must exist and point at a built version before the flow deploys;
  `IntegrationAssociation` (CFN) / `aws_connect_bot_association` must authorize the alias and the
  Lambdas on the target instance, or Connect cannot invoke them even with correct ARNs.
