# Lighthouse delivery and private networking: facts for the ADR

## Team and tooling
- 14 engineers in two squads; all code, merge requests and reviews live in GitLab (gitlab.com,
  group harborpoint/lighthouse). Developers do not have console access to prod.
- Accounts: shared-services 111100000002 (ECR, runners), dev 111100000003, prod 111100000004.
  A test account is planned for Q2.
- Today: GitLab CI runs `cdk deploy` per environment with OIDC roles (w1-t1). It works.
- The platform team also knows CodePipeline well; nobody on the squads does.

## Stakeholder positions
- Security: prefers deploys executed inside AWS (CloudTrail for every step, no deploy
  credentials outside AWS at all, even short-lived). Wants a mandatory manual approval before
  prod, recorded by a named approver.
- Audit: one place to answer "who approved what went to prod, and when". Today they read GitLab
  deployment history; they do not want two systems.
- Squad leads: developers must see diff, test and deploy results on the merge request.
- FinOps: no new always-on infrastructure; pipeline cost should be under USD 100 a month.

## Release model
- Release tags vX.Y.Z; image built and scanned once, promoted by digest across accounts.
- Rollback = move the AgentCore `prod` endpoint to the previous version (w6-c1 runbook).
- Prod change windows: Tue and Thu 10:00-16:00 US Eastern.

## Private networking constraints
- Agent VPCs are isolated (no NAT). Interface endpoints for bedrock-runtime, bedrock-agentcore,
  ECR, logs and STS exist (w3-c1). Endpoint policies are default (full access) today.
- Security wants endpoint policies that allow only the org (`aws:PrincipalOrgID`) and only the
  actions the platform uses.
- The portal calls the AgentCore Runtime endpoint with OAuth bearer tokens (JWT inbound auth),
  not SigV4. AgentCore docs: VPC endpoint policies can only match IAM principals, so OAuth
  (bearer token) calls through the endpoint need `"Principal": "*"` in the policy statement
  that allows them.
- SCP from w1-c1 denies Bedrock and InvokeAgentRuntime in prod unless `aws:SourceVpce` is one
  of the prod endpoints.
