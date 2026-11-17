# aiarch/w1-c1 - Lighthouse org guardrails: five SCPs and one RCP

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 1 (Mon: Organizations and OU design; Tue: SCPs and RCPs; Wed: agent-relevant guardrails; Thu: Identity Center)

## Scenario

Harbor Point Mutual (HPM, fictional) is building **Lighthouse**, an internal agent platform on
Amazon Bedrock AgentCore. The cloud platform team owns a fresh AWS organization
(`o-hpm4k2x9qa`, management account `111100000000`) with this layout (`org/layout.json`):

```text
Root
  Security        111100000001 security-tooling (org CloudTrail bucket lives here)
  Infrastructure  111100000002 shared-services (ECR, GitLab runners)
  Workloads
    Dev           111100000003 lighthouse-dev
    Prod          111100000004 lighthouse-prod
  Sandbox         111100000005 sandbox-agents
  Suspended
```

Security has signed off the guardrails below, but nobody has written them. They must go in as
code so the change board can review a diff, and they must be proven against a request table
before anything is attached in the real org, because a bad SCP locks out every account under it.

You do not have an AWS organization here. `scpsim/` is a small evaluator that applies SCP and
RCP semantics to request fixtures (read its docstring: attachment path, FullAWSAccess, the
management account and service-linked roles, condition operators and missing keys). It works as
shipped; do not change it.

## Requirements

Write the policies in `policies/` and attach them in `policies/attachments.json`. Deny-list
strategy: `FullAWSAccess` stays attached on every target, and every statement you write is a
`Deny` with an alphanumeric `Sid`.

1. **`scp-region-guardrail`** (Root). Deny everything outside `us-east-1` and `us-east-2`,
   except global services (at least `iam`, `organizations`, `sts`, `support`, `budgets`, `ce`,
   `cloudfront`, `route53`, `health`, `account`, `sso`). Lighthouse calls Claude through the
   **US cross-Region inference profiles**, which route requests to `us-east-1`, `us-east-2` or
   `us-west-2`: `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` must work in
   `us-west-2` **only** when the request came through a US inference profile
   (`bedrock:InferenceProfileArn` like `arn:aws:bedrock:*:*:inference-profile/us.*`), and
   nowhere else outside the two home regions.
2. **`scp-protect-audit`** (Root). Deny stopping, deleting or changing the org trail
   (`cloudtrail:StopLogging`, `DeleteTrail`, `UpdateTrail`, `PutEventSelectors`,
   `PutInsightSelectors`) and deny deleting objects, deleting the bucket, or changing the
   policy, lifecycle or versioning of buckets named `hpm-org-cloudtrail-*`.
3. **`scp-org-membership`** (Root). Deny `organizations:LeaveOrganization`. People reach AWS
   through IAM Identity Center only: deny `iam:CreateUser`, `iam:CreateAccessKey` and
   `iam:CreateLoginProfile`.
4. **`scp-bedrock-models`** (Workloads and Sandbox, not Root). Deny `bedrock:InvokeModel` and
   `bedrock:InvokeModelWithResponseStream` on anything that is not an approved model:
   foundation models `anthropic.claude-sonnet-4-5-*`, `anthropic.claude-haiku-4-5-*`,
   `amazon.nova-lite-*`, and inference profiles `us.anthropic.claude-sonnet-4-5-*`,
   `us.anthropic.claude-haiku-4-5-*`.
5. **`scp-prod-private-bedrock`** (Prod). Deny model invocation and
   `bedrock-agentcore:InvokeAgentRuntime` unless the call arrives through one of the two prod
   interface endpoints (`aws:SourceVpce`: `vpce-0a1b2c3d4e5f60001`, `vpce-0a1b2c3d4e5f60002`).
6. **`rcp-org-boundary`** (Root, an RCP). Deny access to S3, `sts:AssumeRole`, KMS, Secrets
   Manager and SQS resources in the org by principals outside `o-hpm4k2x9qa`, unless the
   caller is an AWS service principal. GitLab deploys with OIDC
   (`sts:AssumeRoleWithWebIdentity`, a web identity that has no org ID) must keep working.
   RCP statements use `"Principal": "*"`.
7. **Break-glass.** Requirements 1, 2, 3 and 5 exempt the role named `hpm-breakglass` in any
   member account (match on `aws:PrincipalArn`).
8. Every policy stays under the 5,120-character SCP/RCP size limit.

## Acceptance criteria (what the grader checks)

- The visible request table (`tests/requests_visible.json`) and a larger hidden table
  (cross-Region inference destinations, global services on regional endpoints, management
  account, service-linked roles, OIDC web identity, AWS service principals, break-glass
  scoping) give the expected decision.
- Structure: deny-only custom statements with Sids, FullAWSAccess on every target, size
  limits, RCP principal and supported services, the model allow-list not attached at Root.
- `ANSWER.md` explains your rollout plan (how you would test these on a real org without
  locking anyone out) and the two or three trade-offs you made.

## How to run

```bash
make setup     # builds aiarch/.venv once (uv)
make sim       # per-request decision table: ok / MISMATCH, and which Sid denied
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade aiarch/w1-c1
make clean
```

## What to submit

`policies/*.json`, `policies/attachments.json` and `ANSWER.md`.
