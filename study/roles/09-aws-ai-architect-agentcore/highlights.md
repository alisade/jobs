# Role 9: AWS AI Architect (Agentic AI, AgentCore, Cloud): highlights

The posting is in [posting.md](posting.md). The full material list with links is in [details.md](details.md).

This track sits on top of two others. From the [shared core](../../shared/highlights.md) you need
[section 2](../../shared/details.md#2-agent-design-patterns-and-context-engineering) (agent patterns),
[section 4](../../shared/details.md#4-mcp-model-context-protocol) (MCP),
[section 5](../../shared/details.md#5-verification-and-evals) (evals) and
[section 6](../../shared/details.md#6-llm-security) (LLM security). From role 4 you need
[section 1](../04-aws-fde-agentic-ai/details.md#1-amazon-bedrock-converse-api-tools-guardrails) (Bedrock
Converse, tools, Guardrails) and
[section 2](../04-aws-fde-agentic-ai/details.md#2-amazon-bedrock-agentcore) (the AgentCore overview).
This track does not repeat them. It goes deeper on the parts this posting names: Strands, Runtime as a
container workload, Gateway, OBO identity, Cedar, AgentOps, and the multi-account and pipeline platform
underneath.

## Where you start

This is likely the strongest match of all the roles you are applying to. The posting says it twice:
"Cloud engineering and DevOps capabilities are the primary focus of this role", and the first required
block is labelled "Mandatory & Critical". That block is mostly your day job.

| Posting asks for | You already have |
|---|---|
| Secure, scalable, multi-account AWS environments | Daily work across dev, test, mgmt and prod accounts: cross-account roles, SAML federation, least-privilege identity policies, CloudTrail |
| AWS CDK & CDK Pipelines, automated CDK deployment | CDK in TypeScript: multi-stack apps, fail-fast env context, L2-vs-L1 judgement. CDK Pipelines specifically: no |
| GitLab CI/CD and AWS-native deployment services | CodeBuild, CodePipeline, GitHub Actions on CodeBuild runners, Jenkins. GitLab CI/CD specifically: no |
| Docker & Amazon ECR, containerized workloads | Docker images and ECR for EKS fleets; Helm and ArgoCD releases |
| CloudWatch + OTEL + CloudTrail, monitoring, troubleshooting | CloudWatch alarms and dashboards, CloudTrail investigations, SNS alerting, P1 incident work. OTEL tracing for agents: no |
| Production deployment & release management | Release management and promotion pipelines across environments, backups before every live mutation |
| AWS Organizations / SCPs, IAM Identity Center | You work inside accounts that SCPs and federation govern. Authoring SCPs at org level and administering Identity Center: not on your record |
| VPC endpoints / PrivateLink | Networking around EKS and Lambda. Endpoint policies and PrivateLink for Bedrock/AgentCore: new |
| SSM for operational automation | Operational automation in Jenkins, bash and Step Functions. SSM Automation runbooks: not on your record |
| DynamoDB | Access-pattern-first data modeling: thin |
| MCP integrations with enterprise systems | A daily Claude Code harness with MCP servers for Jira, Spacelift and AWS, used as a consumer. Building MCP servers: no |
| AgentOps, platform operations | You operate platforms for a living; skills, hooks and permission modes in your own agent harness |
| Strands, AgentCore Runtime and Gateway, Cedar, OAuth OBO | Not yet. This is the gap |
| Lambda, Step Functions, Kubernetes/EKS (nice to have) | Production Lambda, Step Functions, Kinesis/Firehose, EKS fleets with access entries |

## Honest fit note

- **The posting weights the part you already have.** Lead with it. The interview will spend real time on
  multi-account design, pipelines, IAM, release management and troubleshooting, and you can go deeper on
  those than most candidates who come from the AI side.
- **The gap is the agentic layer, and it is narrow and concrete:** Strands, AgentCore Runtime and Gateway,
  MCP servers you built, Cedar policies, and OAuth on-behalf-of. All of these are new, so nobody has years
  in them; what interviewers want is that you have built and operated them. That is learnable in weeks,
  but it must be shown in a public repo, not described.
- **Do not claim production AgentCore, Strands or Cedar.** Say "I built and run this platform in a
  personal AWS organization" and walk through it. A built repo with pipelines, policies, traces and a cost
  dashboard is stronger evidence than a vague production claim that falls apart under questions.
- **Name the smaller gaps yourself:** GitLab CI/CD (you know CI deeply; the GitLab syntax and OIDC wiring
  are a week), CDK Pipelines, SCP authoring and Identity Center administration, SSM Automation, DynamoDB
  modeling. Each one has a matching piece in the portfolio.
- **Python.** "Strong expertise in Python" is preferred, not required, and Strands, the AgentCore SDK and
  most samples are Python first. Strands also has a TypeScript SDK. Write the agents in Python anyway,
  because that is what the team will read; keep CDK in TypeScript, where you are strong.
- **"AWS Cedar authorization framework"** means Cedar policies, which AWS uses in two places relevant
  here: Policy in AgentCore (Cedar rules on Gateway tool calls) and Amazon Verified Permissions (Cedar for
  application authorization). Know both and when to use which (details section 5).
- **Ask the recruiter:** "Is the AgentCore platform in production today, or is this role building it?",
  "Which IdP issues user tokens, and does it support token exchange?", "Is deployment GitLab CI running
  `cdk deploy`, or CDK Pipelines on CodePipeline with GitLab as the source?"

## Gaps, most important first

1. **AgentCore Runtime and Gateway, built and operated.** Containerized agent on Runtime (ARM64 image in
   ECR, deployed with CDK), Gateway exposing APIs and Lambdas as MCP tools, versions and endpoints for
   rollback. Named in both required blocks.
2. **Strands Agents.** Agents, tools, MCP clients, multi-agent patterns (agents as tools, swarm, graph,
   workflow), model providers, sessions and hooks.
3. **OAuth on-behalf-of and AgentCore Identity.** Inbound JWT, workload identity, RFC 8693 token exchange,
   and why the tool must act as the user and not as the agent.
4. **Cedar.** Policy in AgentCore on Gateway (log-only, then enforce) and Amazon Verified Permissions.
5. **Building MCP servers** for enterprise systems: task-shaped tools, auth, deployment on Runtime or
   behind Gateway.
6. **AgentOps.** OTEL GenAI traces through ADOT into CloudWatch, AgentCore Observability, CloudTrail data
   events, AWS Agent Registry, online evaluations, alarms and runbooks.
7. **Multi-account governance as code.** Organizations, SCPs (and RCPs), Identity Center permission sets,
   VPC endpoints for Bedrock and AgentCore.
8. **GitLab CI/CD with OIDC to AWS, and CDK Pipelines.**
9. **SSM Automation, Parameter Store, Session Manager.**
10. **DynamoDB modeling for agent state**, and cost and performance tuning for agents.

## Six-week plan (after the shared core sections listed above)

| Week | Focus | Output |
|---|---|---|
| 1 | Personal AWS organization: Organizations, OUs, SCPs, Identity Center, CDK bootstrap with trust; GitLab project with OIDC to AWS | Org layout as code, three accounts (shared-services, dev, prod), a GitLab pipeline that runs `cdk diff` in dev with no stored keys |
| 2 | Strands: tools, MCP client, multi-agent patterns, Bedrock provider, sessions, hooks, traces | A two-agent Strands app (orchestrator plus specialist) running locally against Bedrock, with OTEL traces visible |
| 3 | AgentCore Runtime and Gateway: ARM64 Docker build, ECR, `aws-cdk-lib/aws-bedrockagentcore`, versions and endpoints, two Gateway targets | The app on Runtime, deployed by the pipeline; two internal APIs reachable only as Gateway MCP tools |
| 4 | Identity and authorization: inbound JWT, OBO token exchange, Policy in AgentCore (Cedar), Verified Permissions; build one MCP server | Tools act as the calling user; Cedar decides which role may call which tool, first in LOG_ONLY then ENFORCE; one hand-built MCP server behind Gateway |
| 5 | AgentOps: ADOT, Transaction Search, CloudWatch GenAI observability, CloudTrail data events, Agent Registry, online evaluations; DynamoDB session and cost tables | An AgentOps dashboard with latency, errors, tokens and cost per conversation; alarms wired to SNS |
| 6 | SSM Automation runbooks, CDK Pipelines variant, cost tuning (prompt caching, model choice, token budgets), PrivateLink; book the exam | Three runbooks, a cost before/after table, the README and an architecture diagram; exam date set |

Book the DevOps Engineer - Professional exam in week 1 so the date drives the study
(see [details section 13](details.md#13-certifications-and-how-to-present-the-background)).

## Portfolio project: an enterprise agent platform starter on AWS

One public repo, CDK in TypeScript, agents in Python, synthetic data only. It should read like the
platform this team is about to build.

- **Multi-account foundation:** Organizations with OUs (security, shared-services, workloads/dev,
  workloads/prod), SCPs (region allow-list, deny leaving the org, deny disabling CloudTrail, deny Bedrock
  model invocation outside approved models) and an RCP, Identity Center permission sets for platform-admin,
  agent-developer and read-only. CDK has only L1 constructs for Organizations and Identity Center; say so
  in the README and wrap them in your own small constructs.
- **Pipeline:** GitLab CI/CD with OIDC to a deploy role per account (no stored keys), stages for lint,
  unit tests, `cdk synth`, ARM64 image build and scan, push to ECR, `cdk diff` posted to the merge request,
  deploy to dev, manual approval through a protected environment, deploy to prod. A second branch shows
  the same app on CDK Pipelines with GitLab as the source through CodeConnections, with a short ADR on
  which one you would pick and why.
- **Agents:** a Strands multi-agent app (an orchestrator plus two specialists, for example "IT requests"
  and "access reviews"), packaged with Docker to ECR and run on AgentCore Runtime with versions and a
  `prod` endpoint, so rollback is moving the endpoint.
- **Tools:** AgentCore Gateway exposing two internal APIs as MCP tools: one OpenAPI service on API Gateway
  and one Lambda. Plus one MCP server you wrote yourself, hosted on Runtime and added as a Gateway target.
- **Identity:** users sign in through an IdP that supports token exchange; the agent gets a scoped
  downstream token through AgentCore Identity OBO, so the tool API sees the user, not the agent, and its
  own authorization still applies.
- **Authorization:** Policy in AgentCore with Cedar rules deciding which role may call which tool, with
  input conditions (for example "access-review approvals only for your own team"). Rolled out in LOG_ONLY,
  then ENFORCE, with the decision log as evidence.
- **State:** DynamoDB for session metadata, a per-conversation cost ledger and idempotency keys; AgentCore
  Memory for conversation memory. A one-page note on which data lives where and why.
- **AgentOps:** OTEL traces through ADOT into CloudWatch, a dashboard with p50/p95 latency, tool error
  rate, Cedar denies, tokens and cost per conversation; CloudTrail data events for Gateway; agents and the
  MCP server published in AWS Agent Registry; an online evaluation on a sample of traffic.
- **Operations:** SSM Automation runbooks for "roll back the agent endpoint", "rotate the OAuth client
  secret" and "drain: stop new sessions and wait for running ones", each with an approval step and a
  backup of current state before it changes anything.
- **Private networking:** VPC endpoints for Bedrock, AgentCore and DynamoDB, with endpoint policies.

Keep the bill small: on-demand DynamoDB, short log retention, a budget alarm, and a `make destroy` for the
workload accounts. Do not include any GSA or Lakeview specifics.

## One-line pitch

"I have built and run multi-account AWS platforms, CDK pipelines and production releases for 26 years;
I have put AgentCore, Strands, MCP and Cedar on that same foundation in a public repo, with the user's
identity flowing to every tool call and a trace and a cost for every conversation."
