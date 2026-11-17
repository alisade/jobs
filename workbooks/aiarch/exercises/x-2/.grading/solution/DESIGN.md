# ADR-007: How Lighthouse deploys to AWS, and how the agent VPC endpoints are locked down

## Context

Lighthouse deploys today from GitLab CI: each environment job assumes an OIDC role and runs
`cdk deploy`. It works and developers see results on the merge request. Security wants deploys
executed inside AWS with no deploy credentials outside AWS and a named approver before prod.
Audit wants one place to answer who approved what. FinOps caps pipeline cost at USD 100 a month
and rules out always-on infrastructure. A test account arrives in Q2, so whatever we pick must
add an environment cheaply.

## Options

| | A GitLab-native | B CDK Pipelines (CodeConnections) | C Hybrid |
|---|---|---|---|
| Flow | MR pipeline, tag pipeline runs cdk deploy per env | push to main/tag triggers self-mutating CodePipeline, waves per Stage | GitLab MR checks (test, synth, diff comment); deploy in CodePipeline triggered by tag |
| Approval | GitLab protected environment | CodePipeline manual approval (IAM principal) | CodePipeline manual approval |
| Audit trail | GitLab deployments + CloudTrail of the OIDC role | CodePipeline history + CloudTrail | CodePipeline for deploys, GitLab for code review, linked by commit and tag |
| Credentials | short-lived OIDC tokens leave AWS (job runs outside) | none outside AWS | none outside AWS for deploys |
| Cost | runner minutes only | about USD 1 per pipeline per month plus CodeBuild minutes | same as B |
| Effort | done | new, platform team knows CodePipeline | moderate: keep MR jobs, move deploy |

## Decision

Option C. Security's two hard requirements (in-AWS execution, named approver) are met by
CodePipeline's manual approval and execution in shared-services; developers keep MR feedback in
GitLab. Audit gets one deploy record (CodePipeline), with GitLab linking to it from the
deployment page. We give up the single-tool simplicity of option A and accept a second console
for the platform team.

## Release flow

```text
MR -> GitLab: unit, cdk synth, cdk diff comment, image build (arm64) + scan
tag vX.Y.Z -> GitLab pushes image to ECR (shared-services), records digest
CodeConnections -> CDK Pipeline (shared-services): synth, assets, deploy dev (wave 1)
  -> manual approval (release-managers role, change window Tue/Thu 10-16 ET)
  -> deploy prod (runtime by digest, prod endpoint pinned in config)
rollback: SSM Lighthouse-RollbackAgentEndpoint moves prod back to the previous version
```

## Private networking and endpoint policies

bedrock-runtime endpoint:

```json
{"Statement": [{"Effect": "Allow", "Principal": "*",
  "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"], "Resource": "*",
  "Condition": {"StringEquals": {"aws:PrincipalOrgID": "o-hpm4k2x9qa"}}}]}
```

bedrock-agentcore endpoint: one statement for SigV4 callers conditioned on aws:PrincipalOrgID,
and one for bearer-token callers:

```json
{"Effect": "Allow", "Principal": "*", "Action": "bedrock-agentcore:InvokeAgentRuntime",
 "Resource": "arn:aws:bedrock-agentcore:us-east-1:111100000004:runtime/lighthouse_helpdesk_prod-*"}
```

The bearer-token statement cannot use principal conditions because the endpoint sees no IAM
principal for a JWT caller; it is scoped by resource instead, and the runtime's JWT authorizer
does the identity check. The SCP on aws:SourceVpce still binds every IAM caller. Test plan: a
SigV4 call from inside the VPC (allowed), from a non-org account through the endpoint (denied),
a JWT call to the prod runtime (allowed), a JWT call to another runtime ARN (denied).

## Consequences and follow-ups

Developers lose `cdk deploy` from CI for prod but keep diffs on MRs. Security gets in-AWS
execution. Risk: two systems to operate; mitigated by linking runs by tag. Revisit in Q2 when the
test account is added (a new Stage in the pipeline), and if GitLab-hosted ARM runners make
builds cheaper.
