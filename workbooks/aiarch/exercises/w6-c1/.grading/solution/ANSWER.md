# ANSWER: aiarch/w6-c1

## Approach

Read, no-op check, backup, approve, move, wait, verify. The backup and the no-op come before the
approval so the approver sees real versions and nobody is paged for a rollback that is not needed.

## Fix

Implemented the step graph with validated parameters; verified with make test.

## Trade-offs / what I would do in production

- Assume role: `bedrock-agentcore:GetAgentRuntimeEndpoint` and `UpdateAgentRuntimeEndpoint` on
  the one runtime ARN, `s3:PutObject` on `rollback/*` in the backup bucket,
  `cloudwatch:GetMetricStatistics` (no resource scoping available), trust `ssm.amazonaws.com`
  with aws:SourceAccount.
- Cross-account: run from shared-services with a target-account execution role
  (AWS-SystemsManager-AutomationExecutionRole pattern), rate control 1 and error threshold 0.
- Deploy the document with CDK (`CfnDocument`, L1 only) and version it with the platform.
- Change Manager adds templates, calendars and approval workflows; worth it once several
  teams run production changes, overkill for one team's rollback.
