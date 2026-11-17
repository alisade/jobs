# aiarch/w3-c1 - Lighthouse runtime and gateway stack in CDK

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 3 (Mon: Runtime contract and ARM64 images; Tue: CDK L2 constructs and versions/endpoints; Wed: Gateway targets; Thu: VPC endpoints)

## Scenario

Harbor Point Mutual's helpdesk agent (a Strands app in an ARM64 container) must move from a
hand-built pilot to a stack the GitLab pipeline can deploy to dev and prod. The image is built
once, scanned and pushed to ECR in shared-services (`111100000002`), and the same immutable
tag is deployed to every account. The agent runs on AgentCore Runtime inside an isolated VPC
(no NAT: everything goes through VPC endpoints) and reaches the user directory only as an MCP
tool behind AgentCore Gateway. Release management is endpoint-based: prod traffic uses the
`prod` endpoint, which points at a pinned runtime version, so a rollback is a one-line config
change.

`config/envs.json` holds every environment value. Synth runs offline with
`aws-cdk-lib/aws-bedrockagentcore` (stable L2 constructs: `Runtime`, `RuntimeEndpoint`,
`Gateway`, `GatewayTarget`) and nothing is deployed.

## Requirements (`lib/app.ts`)

1. **Context, fail fast.** `-c env=<name>` must name an environment in config; `-c imageTag`
   must be `vX.Y.Z` or a 12-40 character hex git sha. Missing or invalid values throw with the
   exact command to fix it (and the available envs). No silent defaults.
2. **Image repo (shared-services stack).** `lighthouse/helpdesk-agent`, immutable tags, scan on
   push, retained on stack deletion, lifecycle rules (expire untagged images after 7 days,
   cap total images), and a repository policy that lets only the dev and prod accounts pull
   (`ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer`, `ecr:BatchCheckLayerAvailability`).
3. **Runtime (per env).** Named `lighthouse_helpdesk_<env>`, image from the shared repo at
   the given tag (`AgentRuntimeArtifact.fromEcrRepository`), environment variables
   `LIGHTHOUSE_ENV` and `MODEL_ID`, VPC network mode.
4. **Execution role.** Trusts `bedrock-agentcore.amazonaws.com` with an `aws:SourceAccount`
   condition. Model access is exactly `bedrock:InvokeModel` and
   `bedrock:InvokeModelWithResponseStream` on the env's inference profile ARN and its
   foundation model ARN (any region, for cross-Region inference). Nothing else Bedrock.
5. **Endpoints from config.** One `RuntimeEndpoint` per `endpoints` entry; a version string
   pins it, `null` leaves it on the latest version (dev: `dev`; prod: `canary` and `prod`
   pinned to `7`).
6. **Network.** Two AZs, isolated subnets only, no NAT gateway or internet gateway; interface
   endpoints with private DNS for Bedrock runtime, AgentCore (`bedrock-agentcore`), ECR API,
   ECR Docker, CloudWatch Logs and STS, behind a security group that accepts only 443 from the
   VPC; an S3 gateway endpoint (ECR layers live in S3).
7. **Gateway.** `lighthouse-tools-<env>` with a custom JWT authorizer (the env's discovery URL
   and audience). One Lambda target `user-directory` (ARM64 Python, `lambda/user-directory`)
   exposing a single tool `find_user` with a required `email` string.
8. **Tags.** `Environment` plus the config tags on everything.
9. **Guard rail.** `NoWildcardActions`, a CDK Aspect applied to the app, adds an error
   annotation to any IAM policy or role with an Allow on `*` or `service:*` actions.

## Acceptance criteria (what the grader checks)

- `aws-cdk-lib/assertions` checks for every requirement, for dev and prod.
- The aspect flags a wildcard role in a separate test stack; your stacks synthesize with no errors.
- `ANSWER.md`: why `fromEcrRepository` with an immutable tag rather than `fromAsset` in a
  pipeline, how rollback works with endpoints, and what you would add before prod (alarms,
  endpoint policies, Policy in AgentCore on the gateway).

## How to run

```bash
make setup                     # npm ci into aiarch/_env (one time), link node_modules
make synth ENV=prod TAG=v2.4.0 # print the runtime template
make test                      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade aiarch/w3-c1
make clean
```

## What to submit

`lib/app.ts` and `ANSWER.md`.
