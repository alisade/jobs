# Larkspur help desk platform: how changes ship today (as of 2026-10)

Collected in discovery interviews with the platform lead (Boston), the Pune flow team lead and the
change manager. Verbatim notes, lightly edited.

## Environments

| Env | AWS account | Connect instance alias | Region | Notes |
|---|---|---|---|---|
| Sandbox | 111122223333 | lfg-helpdesk-sbx | us-east-1 | anyone can edit in the console |
| Dev | 111122223333 | lfg-helpdesk-dev | us-east-1 | Pune and Monterrey build flows here |
| Test | 222233334444 | lfg-helpdesk-test | us-east-1 | UAT by help desk supervisors |
| Prod | 444455556666 | lfg-helpdesk-prod | us-east-1 | 1,100 agents, ~9,000 contacts/day |
| DR | 444455556666 | lfg-helpdesk-dr | us-west-2 | ACGR replica; traffic distribution group 100/0 |

## What is code today

- Instance, hours of operation, queues, routing profiles, security profiles: a CDK app
  (`lfg-connect-infra`, TypeScript), deployed by hand from a laptop with `cdk deploy`.
- Lambdas (Node 22 and one Java 11 function): SAM templates, GitHub Actions on push to main
  deploys to dev only. Test/prod deployed by hand with `sam deploy`.
- Lex bot (HelpDeskBot): edited in the console; exported zip committed "sometimes".
- Flows and modules: built in the dev console, then exported to JSON by a Python script and
  imported into test/prod by `pipeline/release.ts` (see connect/w8-t1 for what that did on
  2026-10-06). No flow is in CloudFormation.
- Prompts (WAV files) uploaded by hand per instance. Contact Lens rules and evaluation forms
  created by hand in each environment.

## Pain points (quotes)

- "We find out a flow is broken when agents complain." (supervisor)
- "Every release is a Tuesday-night CAB with a 40-row spreadsheet of ARNs." (change manager)
- "Pune cannot deploy to test without a Boston engineer awake." (Pune lead)
- "Rollback means someone re-imports last week's JSON and hopes." (platform lead)
- "The DR instance is three releases behind prod and nobody knows." (SRE)
- "We have no idea whether a Lambda change broke a flow until the next day's reports." (SRE)

## Facts to respect (verified against AWS docs, 2026-10)

- CloudFormation has `AWS::Connect::*` types for the instance, queues, routing profiles, hours,
  prompts, quick connects, users, security profiles, phone numbers, rules, evaluation forms,
  views, predefined attributes, traffic distribution groups, integration associations,
  `ContactFlow` and `ContactFlowModule` (plus `ContactFlowModuleAlias`), and `TestCase`.
  There is no CloudFormation type (and no API) for contact flow aliases; contact flow versions
  via API are campaign-flow only. Flow modules have versions and aliases (Nov 2025).
- Native flow testing: a test designer (Nov 2025) and test APIs (`CreateTestCase`,
  `StartTestCaseExecution`, ...) since Feb 2026, `AWS::Connect::TestCase` in CloudFormation.
- Terraform (hashicorp/aws) has `aws_connect_*` resources, including `aws_connect_contact_flow`
  and `aws_connect_contact_flow_module`; it has no flow versions/aliases, views or rules.
- Lambda: versions + aliases, CodeDeploy traffic shifting (canary/linear) via SAM
  `AutoPublishAlias` + `DeploymentPreference`.
- CloudWatch namespace `AWS/Connect` (1-minute data): `ContactFlowErrors`,
  `ContactFlowFatalErrors`, `CallsPerInterval`, `ConcurrentCallsPercentage`, `ThrottledCalls`,
  `MissedCalls`, `QueueSize`, `LongestQueueWaitTime`, ... Flow logs go to the log group
  `/aws/connect/<instance-alias>`.
