# ANSWER: aiarch/w1-c1 Lighthouse org guardrails

## Approach

One concern per policy so each can be attached, tested and rolled back on its own: region,
audit protection, org membership and IAM users at Root; the model allow-list on Workloads and
Sandbox; private-endpoint access on Prod; the org boundary as an RCP at Root. I wrote the deny
statements, then ran `make sim` after each policy and read which Sid denied each request.

## Fix

- `scp-region-guardrail`: region deny with a global-services NotAction list that also excludes
  Bedrock invocation; Bedrock is denied outside the three US inference destinations, and in
  us-west-2 unless `bedrock:InferenceProfileArn` is a `us.*` profile. A direct call has no
  profile ARN, so `StringNotLike` on the missing key is true and the call is denied.
- `scp-protect-audit`: CloudTrail tampering and trail-bucket destruction denied.
- `scp-org-membership`: no leaving the org, no IAM users, access keys or console passwords.
- `scp-bedrock-models`: `NotResource` allow-list of approved model and profile ARNs.
- `scp-prod-private-bedrock`: Bedrock and InvokeAgentRuntime denied unless `aws:SourceVpce` is
  one of the two prod endpoints.
- `rcp-org-boundary`: outside-org principals denied on S3, AssumeRole, KMS, Secrets Manager and
  SQS unless they are AWS services. AssumeRoleWithWebIdentity is deliberately not listed.
- Break-glass via `ArnNotLike aws:PrincipalArn arn:aws:iam::*:role/hpm-breakglass`.

## Trade-offs / what I would do in production

- Roll out on a test OU with one sandbox account, then watch CloudTrail for AccessDenied events
  that name a service control policy for a few days before attaching at Root.
- The global-services list and the inference destinations change; review them each quarter
  against the Bedrock cross-Region inference page.
- SCPs do not touch the management account or service-linked roles, so keep the management
  account empty. Alarm on any break-glass AssumeRole.
- Control Tower would give managed controls and drift detection; hand-written SCPs give
  exact control and reviewable diffs. I would still keep these in a repo either way.
