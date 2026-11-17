# Role 9: AWS AI Architect (Agentic AI, AgentCore, Cloud): details

All links were checked on 2026-11-13. Material for each item in [highlights.md](highlights.md). Every topic
has the same parts: why it matters, what you already have (only where true), what to learn, links, and an
exercise.

Not repeated here:

- Agent patterns: [shared section 2](../../shared/details.md#2-agent-design-patterns-and-context-engineering)
- Tool calling and structured output: [shared section 3](../../shared/details.md#3-tool-calling-and-structured-outputs)
- MCP basics: [shared section 4](../../shared/details.md#4-mcp-model-context-protocol)
- Evals: [shared section 5](../../shared/details.md#5-verification-and-evals)
- Prompt injection and tool scoping: [shared section 6](../../shared/details.md#6-llm-security)
- Bedrock Converse, tool use, Guardrails, prompt caching basics: [role 4 section 1](../04-aws-fde-agentic-ai/details.md#1-amazon-bedrock-converse-api-tools-guardrails)
- AgentCore overview (Runtime, Gateway, Memory, Identity, Observability at intro level): [role 4 section 2](../04-aws-fde-agentic-ai/details.md#2-amazon-bedrock-agentcore)
- Knowledge Bases, RAG and vector stores (nice to have here): [role 4 section 3](../04-aws-fde-agentic-ai/details.md#3-rag-and-vector-stores-on-aws)
- Cognito, JWT authorizers, tenant isolation: [role 4 section 5](../04-aws-fde-agentic-ai/details.md#5-multi-tenant-identity-and-authorization-boundaries)
- Lambda, API Gateway, event-driven error handling (nice to have here): [role 4 section 8](../04-aws-fde-agentic-ai/details.md#8-lambda-api-gateway-and-dynamodb-event-driven-backends)

CDK status note (newer than role 4): the AgentCore L2 constructs have graduated from the alpha package to
`aws-cdk-lib/aws-bedrockagentcore` (Runtime, Gateway, GatewayTarget, Memory, Identity credential providers,
Evaluations). As of aws-cdk-lib 2.277 (checked 2026-11-16) Policy (`PolicyEngine`, `Policy`) is stable too, and
the stable `Gateway` takes a `policyEngineConfiguration` prop that also grants the gateway role its evaluate
permissions. The alpha package README still says Policy "remains in alpha"; trust the stable module. Separately, the AgentCore CLI generates
projects on `@aws/agentcore-cdk` (L3 constructs). Re-check this before you start; it moves fast.

---

## 1. Strands Agents SDK

**Why:** "Build AI agents and multi-agent orchestration workflows using the Strands Framework with AWS
Bedrock AgentCore Runtime & Gateway". Strands is in the required skill list by name.

**Learn:**
- The model-driven loop: an `Agent` with a model, a system prompt and tools; the model decides which tool
  to call; the SDK runs the loop. Read "agent loop" first so you can explain what happens per cycle.
- Tools: `@tool` functions, tools from MCP servers (the MCP client is how a Strands agent consumes Gateway),
  tool results and errors the model can act on.
- Multi-agent patterns, and when to use each:
  - Agents as tools: an orchestrator calls specialists like any tool. Simplest, easiest to trace. Start here.
  - Swarm: specialists hand off to each other autonomously. Flexible, harder to bound and to debug.
  - Graph: a flowchart of agents with LLM decisions at nodes, branching and loops.
  - Workflow: a fixed DAG run as one tool, independent tasks in parallel. Closest to a pipeline.
  - A2A: agents as separate services talking the Agent-to-Agent protocol (AgentCore Runtime can host A2A
    servers).
- Model providers: Bedrock is the default; others (Anthropic, OpenAI, LiteLLM, Ollama and more) exist.
  Know how to pin a model ID or inference profile, set Bedrock prompt caching through the provider, and
  route between models.
- Hooks and interventions: lifecycle events around model and tool calls, human-in-the-loop approval, and
  the vended Cedar authorization intervention (section 5). Hooks are where you put guardrails that must
  not depend on the prompt, the same idea as hooks in your Claude Code harness.
- State and sessions: agent state, conversation management, session managers and storage backends (local
  file, S3, or AgentCore Memory). Multi-agent sessions persist orchestrator state too.
- Observability: Strands emits OpenTelemetry traces with `gen_ai.*` attributes, including token usage and
  cache read/write tokens (section 7).
- Python and TypeScript SDKs both exist. Write agents in Python for this role.
- LangGraph is a nice-to-have in the posting; the Strands "migrate from LangGraph" page is a quick way to
  learn both vocabularies.

**Links:**
- [Strands quickstart overview](https://strandsagents.com/docs/user-guide/sdk/quickstart/overview/)
- [Python quickstart](https://strandsagents.com/docs/user-guide/sdk/quickstart/python/)
- [TypeScript quickstart](https://strandsagents.com/docs/user-guide/sdk/quickstart/typescript/)
- [Agent loop](https://strandsagents.com/docs/user-guide/sdk/agents/agent-loop/)
- [Custom tools](https://strandsagents.com/docs/user-guide/sdk/tools/custom-tools/)
- [MCP tools](https://strandsagents.com/docs/user-guide/sdk/tools/mcp-tools/)
- [Multi-agent patterns](https://strandsagents.com/docs/user-guide/sdk/multi-agent/multi-agent-patterns/)
- [Agents as tools](https://strandsagents.com/docs/user-guide/sdk/multi-agent/agents-as-tools/)
- [Swarm](https://strandsagents.com/docs/user-guide/sdk/multi-agent/swarm/)
- [Graph](https://strandsagents.com/docs/user-guide/sdk/multi-agent/graph/)
- [Workflow](https://strandsagents.com/docs/user-guide/sdk/multi-agent/workflow/)
- [Agent-to-Agent (A2A)](https://strandsagents.com/docs/user-guide/sdk/multi-agent/agent-to-agent/)
- [Model providers](https://strandsagents.com/docs/user-guide/sdk/model-providers/)
- [Amazon Bedrock provider](https://strandsagents.com/docs/user-guide/sdk/model-providers/amazon-bedrock/)
- [Model routing](https://strandsagents.com/docs/user-guide/sdk/model-providers/model-routing/)
- [Hooks](https://strandsagents.com/docs/user-guide/sdk/agents/hooks/)
- [Human-in-the-loop](https://strandsagents.com/docs/user-guide/sdk/agents/interventions/human-in-the-loop/)
- [Agent state](https://strandsagents.com/docs/user-guide/sdk/agents/state/)
- [Session management](https://strandsagents.com/docs/user-guide/sdk/agents/session-management/)
- [Strands evals SDK](https://strandsagents.com/docs/user-guide/evals-sdk/)
- [Migrate from LangGraph](https://strandsagents.com/docs/user-guide/migrate/langgraph/)
- [Strands TypeScript SDK (GitHub)](https://github.com/strands-agents/sdk-typescript)

**Exercise:** Build the portfolio agents locally first. An orchestrator with two specialists as tools
("IT requests" and "access reviews"), each with two `@tool` functions over a fake JSON store. Add a hook
that logs every tool call with its arguments and blocks any tool whose name starts with `delete_`. Then
rebuild the same flow as a Swarm and as a Graph, run the same 10 prompts through all three, and write a
half page comparing answer quality, number of model calls, tokens and how easy each trace was to read.

---

## 2. AgentCore Runtime: containerized agents, Docker, ECR, CDK

**Why:** "Build, package, and deploy AgentCore workloads as containerized applications using Docker and
Amazon ECR" and "Implement Infrastructure as Code (IaC) using AWS CDK".

**You already have:** Docker images, ECR, CDK in TypeScript with multi-stack apps, and release promotion.
The new parts are the Runtime contract and its deployment model.

**Learn:**
- The service contract: an HTTP server with `POST /invocations` and `GET /ping` (port and path can be
  configured), or the MCP, A2A or AG-UI protocol contracts. The AgentCore SDK's `BedrockAgentCoreApp`
  wraps this for you; know what it does underneath.
- **ARM64 only.** Runtime requires ARM64 images. In CI that means `docker buildx --platform linux/arm64`
  with QEMU on x86 runners, or native ARM runners (CodeBuild ARM, GitLab ARM runners). This is the first
  thing that breaks a pipeline written for x86.
- Packaging choices: container image from ECR, or direct code deployment (zip, Python or Node.js). The
  posting asks for containers; know that the other exists.
- Sessions: each session runs in an isolated microVM; sessions last up to 8 hours per lifecycle on
  microVMs (longer on the newer Instances option); idle timeout and lifecycle settings; `HealthyBusy`
  pings for background work; long-running and async agents.
- Execution role permissions, inbound auth (SigV4 or JWT), custom header allowlist for passing context.
- Versions and endpoints: every update creates a version; endpoints point at versions. Rollback is moving
  `prod` back to the previous version. This is your release management story on AgentCore.
- VPC configuration for Runtime (section 8), and security best practices.
- Runtime vs the newer AgentCore harness (a managed agent loop where you supply configuration instead of
  code). Know the trade-off; the posting is about Runtime with Strands, so build on Runtime.
- CDK, after checking L2 vs L1 as you always do:
  - `aws-cdk-lib/aws-bedrockagentcore` has stable L2s: `Runtime`, `RuntimeEndpoint`, and
    `AgentRuntimeArtifact.fromAsset()` (CDK builds and pushes the image as an asset) or
    `fromEcrRepository(repo, tag)` (the pipeline builds and pushes; CDK only references the tag).
  - For a real pipeline prefer `fromEcrRepository` with an immutable tag: the image is built, scanned and
    promoted once, and the same digest goes to every account. `fromAsset` rebuilds per synth.
  - The AgentCore CLI scaffolds projects on `@aws/agentcore-cdk` L3 constructs; you can add your own
    resources to the generated stack.
- ECR: image scanning, lifecycle policies, immutable tags, cross-account pull for promotion.

**Links:**
- [AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html)
- [Runtime service contract](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-service-contract.html)
- [Get started without the AgentCore CLI (FastAPI, Docker, ARM64)](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/getting-started-custom.html)
- [Get started with the AgentCore CLI in TypeScript](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-cli-typescript.html)
- [Runtime IAM permissions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html)
- [Runtime sessions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-sessions.html)
- [Long-running and async agents](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-long-run.html)
- [Pass custom headers](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-header-allowlist.html)
- [Runtime versioning and endpoints](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agent-runtime-versioning.html)
- [Runtime security best practices](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-security-best-practices.html)
- [Runtime troubleshooting](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-troubleshooting.html)
- [Harness vs Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-vs-runtime.html)
- [Customize the AgentCore CLI's CDK code](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/customize-project-cdk-code.html)
- [CDK aws-bedrockagentcore (stable L2)](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_bedrockagentcore-readme.html)
- [CDK AgentCore alpha (older construct docs)](https://docs.aws.amazon.com/cdk/api/v2/docs/@aws-cdk_aws-bedrock-agentcore-alpha-readme.html)
- [CDK ECR assets](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ecr_assets-readme.html)
- [Strands: deploy to AgentCore](https://strandsagents.com/docs/user-guide/sdk/deploy/deploy_to_bedrock_agentcore/)
- [Strands: operating agents in production](https://strandsagents.com/docs/user-guide/sdk/deploy/operating-agents-in-production/)
- [Docker multi-platform builds](https://docs.docker.com/build/building/multi-platform/)
- [What is Amazon ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html)
- [ECR image scanning](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html)
- [ECR lifecycle policies](https://docs.aws.amazon.com/AmazonECR/latest/userguide/LifecyclePolicies.html)
- [AgentCore CLI (GitHub)](https://github.com/aws/agentcore-cli)
- [AgentCore samples (GitHub)](https://github.com/awslabs/agentcore-samples)

**Exercise:** Package the section 1 app as an ARM64 image built on an x86 machine with buildx. Push it to
ECR with an immutable tag. In CDK, create the Runtime with `fromEcrRepository`, a `dev` and a `prod`
`RuntimeEndpoint`, and a least-privilege execution role (Bedrock invoke on one inference profile only).
Deploy v1, then v2 with a deliberate bug, then roll `prod` back to v1 by changing only the endpoint, and
time it. Write down cold start, p50 latency and what you saw in the logs when v2 failed.

---

## 3. AgentCore Gateway: APIs and Lambdas as MCP tools

**Why:** "AWS Bedrock AgentCore Gateway" is required, and "Integrate Bedrock foundation models with
enterprise applications and APIs" and "REST APIs & Microservices Integration" are how you get there.

**You already have:** Lambda, IAM and API work. Gateway is a managed MCP front door to those.

**Learn:**
- Concepts: a gateway is one MCP endpoint; targets behind it become tools. Target types: Lambda, OpenAPI
  schema, API Gateway stage, Smithy model, existing MCP servers, built-in connectors (Knowledge Bases, Step
  Functions, web search), plus HTTP and inference targets.
- Tool naming: how target and tool names combine, and why names and descriptions are prompts the model
  reads (see [shared section 2](../../shared/details.md#2-agent-design-patterns-and-context-engineering)).
- Inbound auth (who may call the gateway: JWT from your IdP, or IAM) and outbound auth (how the gateway
  calls the target: IAM role, API key, OAuth from the Identity token vault).
- Semantic tool search: with dozens of tools, the agent searches instead of loading every schema.
- Interceptors (request/response hooks), rate limits, WAF integration, custom domains, MCP sessions and
  streaming.
- Debugging: debug messages, MCP Inspector against the gateway, CloudTrail data events for tool calls.
- Policy in AgentCore attaches here (section 5).
- CDK: `Gateway`, `GatewayTarget`, `GatewayAuthorizer`, `GatewayCredentialProvider` are stable L2s in
  `aws-cdk-lib/aws-bedrockagentcore`.

**Links:**
- [AgentCore Gateway](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html)
- [Gateway core concepts](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-core-concepts.html)
- [Supported targets](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-supported-targets.html)
- [Lambda targets](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-add-target-lambda.html)
- [OpenAPI targets](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-schema-openapi.html)
- [API Gateway stage targets](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-api-gateway.html)
- [MCP server targets](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-MCPservers.html)
- [Tool naming](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-tool-naming.html)
- [Inbound authorization](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-inbound-auth.html)
- [Outbound authorization](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-outbound-auth.html)
- [Semantic tool search](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-using-mcp-semantic-search.html)
- [Interceptors](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-interceptors.html)
- [Rate limits](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-rate-limits.html)
- [Use the MCP Inspector](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-using-inspector.html)
- [Gateway and CloudTrail](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-cloudtrail.html)

**Exercise:** Put two internal APIs behind one gateway: an "access request" REST service on API Gateway
(OpenAPI target) and a "user directory" Lambda (Lambda target). Require a JWT on inbound. Connect the
Strands orchestrator to the gateway as an MCP client and remove its local tools. List tools with the MCP
Inspector, then break it three ways (wrong audience in the JWT, missing outbound permission, a schema the
model misuses) and record each error and where you saw it.

---

## 4. AgentCore Identity and OAuth on-behalf-of (OBO)

**Why:** "Implement secure authentication and authorization using OAuth/OBO patterns", and "OAuth / OBO
Authentication" is in the mandatory list.

**You already have:** IAM roles and SAML federation, so you know delegation, trust and audience. OAuth 2.0
flows and token exchange are the new layer.

**Learn:**
- OAuth 2.0 basics you must be able to whiteboard: authorization code with PKCE, client credentials,
  access token vs ID token, audience and scopes, JWT access token claims.
- The agent problem: a user asks the agent to do something; the tool must act as that user with that
  user's permissions, not with a broad agent service account. Otherwise the agent is a confused deputy.
- OBO with token exchange: the agent exchanges the user's inbound token for a new token aimed at the
  downstream API. RFC 8693 (token exchange: `subject_token` is the user, optional `actor_token` is the
  agent) and the RFC 7523 JWT-bearer form that Microsoft Entra ID uses for its OBO flow.
- How AgentCore Identity does it:
  - Inbound JWT authorizer on Runtime or Gateway validates the user token.
  - A workload identity for the agent; `GetWorkloadAccessTokenForJWT` binds the user token to it.
  - An OAuth2 credential provider configured with an on-behalf-of mode (`TOKEN_EXCHANGE` with an actor
    token from M2M, an AWS-issued JWT, or none; or `JWT_AUTHORIZATION_GRANT`).
  - `GetResourceOauth2Token` with `ON_BEHALF_OF_TOKEN_EXCHANGE` returns the downstream token. The agent
    code never sees client secrets; the IdP makes the final decision on scopes and delegation.
  - Other patterns in the same service: user-consent (3-legged) OAuth with session binding, M2M, API keys
    in the token vault, scoping which agent may use which credential provider.
- The IdP decides what is possible. Confirm that yours supports token exchange (or the Entra OBO form)
  before you design around it; this is a recruiter question too.
- MCP authorization: the MCP spec's OAuth model (protected resource metadata RFC 9728, resource
  indicators RFC 8707), so an MCP server you build (section 6) validates audience correctly.
- Rule to state in interviews: identity comes from the verified token, never from tool arguments the
  model produced (role 4 section 5 covers the tenant version of this).

**Links:**
- [AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html)
- [Identity terminology](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity-terminology.html)
- [Understanding agent identities](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/understanding-agent-identities.html)
- [Inbound JWT authorization](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/inbound-jwt-authorizer.html)
- [Credential providers](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity-outbound-credential-provider.html)
- [Supported authentication patterns](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/common-use-cases.html)
- [On-behalf-of token exchange](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/on-behalf-of-token-exchange.html)
- [Get workload access token](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/get-workload-access-token.html)
- [OAuth authorization URL session binding](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/oauth2-authorization-url-session-binding.html)
- [Scope credential access](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/scope-credential-provider-access.html)
- [Runtime inbound and outbound auth](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-oauth.html)
- [Provider setup: Okta](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity-idp-okta.html)
- [Provider setup: Microsoft](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity-idp-microsoft.html)
- [Provider setup: Cognito](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity-idp-cognito.html)
- [RFC 6749: OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749)
- [RFC 7636: PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [RFC 8693: OAuth 2.0 Token Exchange](https://datatracker.ietf.org/doc/html/rfc8693)
- [RFC 7523: JWT profile for OAuth 2.0 grants](https://datatracker.ietf.org/doc/html/rfc7523)
- [RFC 9068: JWT profile for access tokens](https://datatracker.ietf.org/doc/html/rfc9068)
- [RFC 8707: Resource indicators](https://datatracker.ietf.org/doc/html/rfc8707)
- [RFC 9728: Protected resource metadata](https://datatracker.ietf.org/doc/html/rfc9728)
- [Microsoft identity platform OBO flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-on-behalf-of-flow)
- [MCP authorization spec](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)

**Exercise:** Draw the full token path for one request in the portfolio: user signs in, Runtime validates
the JWT, the agent calls Gateway, the tool needs a token for the access-request API. Mark every token,
its issuer, audience and subject. Then build it: configure an OAuth2 credential provider with an OBO mode
your IdP supports, call the downstream API with the exchanged token, and have the API log `sub` and the
actor claim. Prove two things in a test: user A's request reaches the API as user A, and replaying user
A's original token directly against the API fails on audience.

---

## 5. Cedar: Policy in AgentCore and Amazon Verified Permissions

**Why:** "Apply security and governance policies using AWS Cedar authorization framework" and "Cedar
Policy Framework" in the mandatory list.

**You already have:** IAM policy evaluation (explicit deny wins, default deny), OPA/Rego policy work on
Spacelift. Cedar has the same default-deny, forbid-wins model with a different syntax.

**Learn:**
- Cedar basics: `permit` and `forbid` over principal, action, resource and context; `when` and `unless`
  conditions; entities with attributes and parents; schemas and validation; analysis that proves a
  policy set always allows or never allows something.
- **Policy in AgentCore** (the "AWS Cedar" part most relevant here):
  - A policy engine attached to a Gateway evaluates every tool call. Principals are
    `AgentCore::OAuthUser` (from the JWT, with claims as tags) or `AgentCore::IamEntity`; actions are the
    gateway's tools; the schema is generated from the tool definitions, so tool input parameters are
    usable in conditions.
  - Modes: `LOG_ONLY` (evaluate and trace, do not enforce) and `ENFORCE`. Roll out in log-only, read the
    decisions, then enforce. Same habit as dry-run first.
  - Extras: natural-language policy authoring, guardrail signals inside policies, and temporal policies
    over a policy session (for example "only after an approval earlier in the session"). The docs now
    recommend writing in Dogwood, a Cedar-compatible superset that adds those condition blocks; plain
    Cedar policies keep working.
  - CDK: `PolicyEngine` and `Policy` are stable in `aws-cdk-lib/aws-bedrockagentcore` (2.277); attach the
    engine with the `Gateway` prop `policyEngineConfiguration`, which also grants the gateway role the
    evaluate permissions. Older posts show an L1 escape hatch on `CfnGateway`; you no longer need it.
- **Amazon Verified Permissions (AVP):** managed Cedar for your own applications. Policy stores, schemas,
  identity sources (Cognito or OIDC), `IsAuthorized` and `IsAuthorizedWithToken`. Use it inside a tool API
  that needs fine-grained decisions on its own resources. CDK has only L1 constructs for AVP in
  `aws-cdk-lib`; a cdklabs L2 package exists but is pre-1.0.
- Which one where: Policy in AgentCore answers "may this user's agent call this tool with these
  arguments". AVP answers "may this user do this to this record" inside the API. In a real platform you
  often want both, plus IAM underneath.
- Strands also ships a Cedar authorization intervention that checks policies before each tool call inside
  the agent process. Useful for local tools that never pass through Gateway.

**Links:**
- [Cedar](https://cedarpolicy.com/)
- [Cedar docs](https://docs.cedarpolicy.com/)
- [Cedar terminology](https://docs.cedarpolicy.com/overview/terminology.html)
- [Cedar policy syntax](https://docs.cedarpolicy.com/policies/syntax-policy.html)
- [Cedar policy examples](https://docs.cedarpolicy.com/policies/policy-examples.html)
- [Cedar schema](https://docs.cedarpolicy.com/schema/schema.html)
- [Cedar authorization semantics](https://docs.cedarpolicy.com/auth/authorization.html)
- [Policy in AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html)
- [Policy core concepts (Cedar, Dogwood, schema, analysis)](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-core-concepts.html)
- [Getting started with Policy](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-getting-started.html)
- [Policy conditions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-conditions.html)
- [Authorization flow](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-authorization-flow.html)
- [Enforcement modes](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-enforcement-modes.html)
- [Test a policy in LOG_ONLY mode](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-test-a-policy.html)
- [Policy authoring guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-authoring-guide.html)
- [Principal-scoped policy examples](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/example-policies-principal.html)
- [Temporal policies](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-temporal.html)
- [Writing policies in natural language](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-natural-language.html)
- [Dogwood policy language](https://dogwood-policy.github.io/dogwood/index.html)
- [What is Amazon Verified Permissions](https://docs.aws.amazon.com/verifiedpermissions/latest/userguide/what-is-avp.html)
- [AVP terminology](https://docs.aws.amazon.com/verifiedpermissions/latest/userguide/terminology.html)
- [AVP policy stores](https://docs.aws.amazon.com/verifiedpermissions/latest/userguide/policy-stores.html)
- [AVP identity sources](https://docs.aws.amazon.com/verifiedpermissions/latest/userguide/identity-sources.html)
- [IsAuthorizedWithToken API](https://docs.aws.amazon.com/verifiedpermissions/latest/apireference/API_IsAuthorizedWithToken.html)
- [CDK aws-verifiedpermissions (L1)](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_verifiedpermissions-readme.html)
- [Strands Cedar authorization](https://strandsagents.com/docs/user-guide/sdk/agents/interventions/cedar-authorization/)

**Exercise:** Write a Cedar policy set for the portfolio gateway with three roles from a JWT claim:
`employee` may call `create_access_request` only for themselves; `manager` may call
`approve_access_request` only when the request's team equals their team claim; `auditor` may call only
read tools; and a `forbid` that blocks any approval outside business hours. Deploy in LOG_ONLY, replay 20
scripted requests, check every decision in the logs against what you expected, then switch to ENFORCE.
Add an AVP check inside the access-request API for the same "own team" rule and explain in the README why
both layers exist.

---

## 6. Building MCP servers for enterprise systems

**Why:** "Develop and manage MCP (Model Context Protocol) integrations with enterprise systems and
tools." You have used MCP servers daily; this posting wants someone who builds and operates them.

**You already have:** real consumer experience with MCP servers for Jira, Spacelift and AWS, including
their failure modes (expired tokens, oversized tool output, mangled formatting). That is a good source of
design rules. [Shared section 4](../../shared/details.md#4-mcp-model-context-protocol) covers the basics.

**Learn:**
- Design tools around tasks, not around one tool per REST endpoint: fewer tools, clear names, small
  outputs, errors the model can act on, pagination.
- Transports: stdio for local use, Streamable HTTP for remote servers; sessions and statelessness.
- Auth on a remote server: the MCP authorization spec (section 4), validating audience, never passing the
  client's token through to the backend unchanged (token passthrough is called out as an anti-pattern in
  the MCP security guidance; use OBO instead).
- Where to run it on AWS:
  - On AgentCore Runtime with the MCP protocol contract (stateless or stateful MCP features).
  - Behind Gateway as an MCP server target, so it shares inbound auth, Cedar policy and logging with the
    other tools.
  - Or skip the server: if the system already has an OpenAPI spec or a Lambda, a Gateway target may be
    enough. Being able to say "we did not need a custom server here" is an architect answer.
- Testing: MCP Inspector, contract tests on tool schemas, a small eval of the model picking the right tool.
- Catalog: publish servers in AWS Agent Registry (section 7) so other teams find them instead of
  rebuilding them.
- OTEL has semantic conventions for MCP spans; emit them (section 7).

**Links:**
- [MCP introduction](https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro)
- [Build an MCP server](https://modelcontextprotocol.io/docs/2026-07-28/develop/build-server)
- [MCP specification](https://modelcontextprotocol.io/specification/2026-07-28)
- [Transports](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)
- [Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [Authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)
- [Security best practices](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices)
- [MCP Inspector](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Deploy MCP servers on AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-mcp.html)
- [Stateful MCP features on Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/mcp-stateful-features.html)
- [Gateway MCP server targets](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-MCPservers.html)
- [OTEL semantic conventions for MCP](https://opentelemetry.io/docs/specs/semconv/gen-ai/mcp/)

**Exercise:** Write a Python MCP server over a mock "change management" system (create change, get change,
list my open changes, add comment) with 4 task-shaped tools, Streamable HTTP, and JWT audience
validation. Deploy it on Runtime, add it to the gateway as an MCP server target, and call it from the
Strands agent. Write a one-page design note listing five rules you learned from the MCP servers you use
every day, and show where each rule appears in this server.

---

## 7. AgentOps: observability, tracing, registry, evaluations

**Why:** "Experience in AgentOps and Platform operations for AgentCore runtime, Agent registry, MCP
integration, OTEL, Ops. Monitoring", "Implement AI observability, operational monitoring, and distributed
tracing", and "CloudWatch + OTEL + CloudTrail" in the mandatory list.

**You already have:** CloudWatch alarms and dashboards, CloudTrail investigations, SNS alerting and years
of incident work. What is new is agent-shaped telemetry: spans per model call and tool call, tokens, and
quality, not just errors and latency.

**Learn:**
- AgentCore Observability: built-in metrics for Runtime, Memory, Gateway, Identity, Policy and built-in
  tools in CloudWatch; the one-time CloudWatch Transaction Search setup (spans stored as structured logs);
  the CloudWatch generative AI observability pages.
- Instrumenting agent code with ADOT (AWS Distro for OpenTelemetry); the same works for agents hosted
  outside AgentCore. X-Ray is the trace backend under Transaction Search; ADOT is the recommended way to
  send to it.
- OTEL GenAI semantic conventions: agent spans, model call spans, `gen_ai.usage.*` token attributes, MCP
  spans. Strands emits these, so the trace already has what a cost dashboard needs.
- What an AgentOps dashboard shows: sessions, p50/p95 latency per agent and per tool, tool error rate,
  throttles, Cedar denies, tokens in/out and cache hits, cost per conversation, evaluation scores.
- Audit: CloudTrail management events for AgentCore, data events for Gateway tool calls, Bedrock model
  invocation logging to S3/CloudWatch. Know what each one records and what it costs.
- Cross-account: CloudWatch cross-account observability so a central ops account sees every workload
  account.
- AWS Agent Registry ("Agent registry" in the posting): a catalog of agents, MCP servers, skills and tools
  with an approval workflow, search, an MCP endpoint, Organizations integration and RAM sharing. It is the
  governance answer to "how do 20 teams find and trust each other's tools".
- AgentCore Evaluations: built-in and custom evaluators, online evaluation on sampled live traffic,
  on-demand and batch runs. Tie them to your eval habits from
  [shared section 5](../../shared/details.md#5-verification-and-evals).
- Runbooks for agent incidents: model throttling, tool backend down, IdP outage, a bad version rolled out,
  cost spike. Each with the metric that detects it and the first three checks.

**Links:**
- [Observe, trace and audit agents](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability.html)
- [Add observability to AgentCore resources](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-configure.html)
- [Observability concepts](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-telemetry.html)
- [Runtime observability data](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-runtime-metrics.html)
- [Gateway observability data](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-gateway-metrics.html)
- [Policy observability data](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-policy-metrics.html)
- [AgentCore cross-account monitoring](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-cross-account.html)
- [CloudWatch Transaction Search](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Transaction-Search.html)
- [CloudWatch generative AI observability](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/GenAI-observability.html)
- [CloudWatch cross-account observability](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Unified-Cross-Account.html)
- [CloudWatch embedded metric format](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html)
- [X-Ray with ADOT](https://docs.aws.amazon.com/xray/latest/devguide/xray-services-adot.html)
- [AWS Distro for OpenTelemetry](https://aws-otel.github.io/docs/introduction/)
- [OTEL GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [OTEL GenAI agent spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/)
- [OTEL GenAI model spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/)
- [OTEL GenAI metrics](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/)
- [Strands observability](https://strandsagents.com/docs/user-guide/sdk/observability-evaluation/observability/)
- [Strands traces](https://strandsagents.com/docs/user-guide/sdk/observability-evaluation/traces/)
- [Strands metrics](https://strandsagents.com/docs/user-guide/sdk/observability-evaluation/metrics/)
- [Gateway CloudTrail data events](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/enabling-cloudtrail-data-event-logging.html)
- [CloudTrail data events](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/logging-data-events-with-cloudtrail.html)
- [Bedrock and CloudTrail](https://docs.aws.amazon.com/bedrock/latest/userguide/logging-using-cloudtrail.html)
- [Bedrock model invocation logging](https://docs.aws.amazon.com/bedrock/latest/userguide/model-invocation-logging.html)
- [AWS Agent Registry](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry.html)
- [Agent Registry record lifecycle](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry-record-lifecycle.html)
- [Agent Registry MCP endpoint](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry-mcp-endpoint.html)
- [Agent Registry with Organizations](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/registry-organizations.html)
- [AgentCore Evaluations](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/evaluations.html)
- [Online evaluation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/online-evaluations.html)

**Exercise:** Enable Transaction Search and instrument the agents with ADOT. Build a CloudWatch dashboard
in CDK with the panels listed above, and alarms (to SNS) for p95 latency, tool error rate, throttles and
hourly cost. Turn on Gateway data events and find one tool call in CloudTrail from its trace ID. Publish
the agents and the MCP server in Agent Registry with an approval step. Then cause two incidents on
purpose (revoke the tool Lambda's permission; push a version with a broken prompt) and write a short
post-incident note for each, starting from the alarm that fired.

---

## 8. Multi-account governance: Organizations, SCPs, Identity Center, PrivateLink

**Why:** "Design build and maintain secure, scalable, multi-account AWS environments", "Support SCP-based
governance controls", and "AWS Organizations / SCPs", "IAM Identity Center", "VPC Endpoints / PrivateLink"
in the mandatory list.

**You already have:** daily work across dev, test, mgmt and prod accounts, cross-account roles, SAML
federation, identity policies and CloudTrail. You have worked under an org's guardrails; authoring them is
the gap.

**Learn:**
- Organizations: management account kept empty, OU design (security, infrastructure, workloads by
  environment, sandbox, suspended), delegated administrators, the multi-account whitepaper. Control Tower
  as the managed option, and why some teams still do it by hand.
- SCPs: they limit the maximum permissions of principals in member accounts and grant nothing; they do
  not affect the management account; deny-list vs allow-list strategy; testing them without locking
  yourself out. RCPs (resource control policies) limit what can be done to resources, for example
  blocking access from outside the org. Declarative policies for service configuration.
- Agent-relevant guardrails: region allow-list that still permits cross-Region inference profiles (check
  the Bedrock docs for which regions an inference profile routes to before you deny them), restrict
  Bedrock to approved model IDs, require VPC endpoints for Bedrock and AgentCore data-plane calls, protect
  CloudTrail and log buckets.
- IAM Identity Center: permission sets mapped to accounts and groups, an external IdP as the source,
  ABAC with user attributes, delegated administration, trusted identity propagation. Know where it stops
  (it is for people into AWS, not your app's end users).
- CDK reality check: Organizations and Identity Center have L1 constructs only in `aws-cdk-lib` (no L2).
  Many teams use Control Tower, Account Factory or Terraform here instead. Wrap the L1s in small
  constructs and say why.
- VPC endpoints and PrivateLink: interface endpoints for Bedrock runtime and AgentCore (data plane
  `com.amazonaws.<region>.bedrock-agentcore`, control plane `...bedrock-agentcore-control`, and the
  gateway endpoint), endpoint policies, `aws:SourceVpce` / `aws:SourceVpc` condition keys. Gotcha from the
  AgentCore docs: endpoint policies can only match IAM principals, so OAuth (bearer token) calls through
  the endpoint need `Principal: "*"` in the policy.
- Runtime and Gateway VPC configuration and Gateway VPC egress, so tools can reach private APIs.

**Links:**
- [What is AWS Organizations](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_introduction.html)
- [Organizing your AWS environment (whitepaper)](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html)
- [AWS Security Reference Architecture](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/)
- [Service control policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html)
- [SCP evaluation](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_evaluation.html)
- [SCP examples](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps_examples.html)
- [Resource control policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html)
- [Declarative policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_declarative_policies.html)
- [Accessing member accounts](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_accounts_access.html)
- [What is Control Tower](https://docs.aws.amazon.com/controltower/latest/userguide/what-is-control-tower.html)
- [IAM policy evaluation logic](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html)
- [Global condition keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html)
- [Service authorization reference: AgentCore](https://docs.aws.amazon.com/service-authorization/latest/reference/list_bedrock-agentcore.html)
- [What is IAM Identity Center](https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html)
- [Permission sets](https://docs.aws.amazon.com/singlesignon/latest/userguide/permissionsetsconcept.html)
- [Identity Center ABAC](https://docs.aws.amazon.com/singlesignon/latest/userguide/abac.html)
- [Identity Center delegated administration](https://docs.aws.amazon.com/singlesignon/latest/userguide/delegated-admin.html)
- [Trusted identity propagation](https://docs.aws.amazon.com/singlesignon/latest/userguide/trustedidentitypropagation-overview.html)
- [CDK aws-organizations (L1 only)](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_organizations-readme.html)
- [CDK aws-sso (L1 only)](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_sso-readme.html)
- [What is PrivateLink](https://docs.aws.amazon.com/vpc/latest/privatelink/what-is-privatelink.html)
- [Endpoint policies](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-access.html)
- [Bedrock interface endpoints](https://docs.aws.amazon.com/bedrock/latest/userguide/vpc-interface-endpoints.html)
- [AgentCore VPC and PrivateLink](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/vpc.html)
- [AgentCore interface endpoints](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/vpc-interface-endpoints.html)
- [AgentCore Runtime VPC configuration](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-vpc.html)
- [AgentCore VPC condition keys](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/security-vpc-condition.html)
- [Gateway VPC egress](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-vpc-egress.html)
- [Bedrock cross-Region inference](https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html)

**Exercise:** In a personal organization (a fresh management account, nothing else in it), create the OUs
and three member accounts. Write four SCPs and one RCP from the highlights list as code, attach them to a
test OU first, and prove each one with a denied CLI call captured in CloudTrail. Set up Identity Center
with three permission sets. Then put VPC endpoints for Bedrock runtime and AgentCore in the dev workload
VPC, and add an SCP condition that denies `bedrock:InvokeModel` unless the call comes through your
endpoint. Back up every policy before you change it, as you do at work.

---

## 9. GitLab CI/CD and CDK Pipelines

**Why:** "Develop and manage CI/CD pipelines using GitLab CI/CD and AWS-native deployment services" and
"AWS CDK & CDK Pipelines", "Production Deployment & Release Management" in the mandatory list.

**You already have:** CodeBuild, CodePipeline, GitHub Actions on CodeBuild runners, Jenkins, CDK with
fail-fast env context, and release promotion across accounts. The concepts transfer; the GitLab syntax
and CDK Pipelines are new.

**Learn:**
- GitLab CI basics: `.gitlab-ci.yml`, stages, jobs, `rules`, `needs` (DAG), artifacts and caches,
  merge request pipelines, parent-child and multi-project pipelines, CI/CD components for reuse,
  variables and protected/masked variables. The GitHub Actions migration page maps concepts you already
  know.
- OIDC to AWS: `id_tokens` in the job, an IAM OIDC provider for your GitLab host, a role per account whose
  trust policy pins `sub` to `project_path:<group>/<project>:ref_type:branch:ref:main` (and the audience),
  `AssumeRoleWithWebIdentity`. No stored keys. Same pattern as GitHub Actions OIDC.
- Environments, protected environments and deployment approvals for prod; who may run which job.
- Building images in GitLab: Docker-in-Docker or rootless Buildah, ARM64 builds for AgentCore (section 2),
  container scanning and secret detection templates.
- Runners: GitLab-hosted, self-managed, and self-managed GitLab runners on CodeBuild (the GitLab version
  of what you run for GitHub Actions).
- Deploying CDK from GitLab: `cdk synth` once, keep `cdk.out` as an artifact, `cdk diff` posted to the MR,
  `cdk deploy --app cdk.out` per environment with that environment's role. Bootstrap trust (`--trust`) so
  the CI role can use the CDK deploy roles in each target account. Your fail-fast `env` context rule
  applies here: call `cdk` directly, not through a wrapper that drops flags.
- CDK Pipelines (`aws-cdk-lib/pipelines`): a self-mutating CodePipeline that synthesizes, publishes assets
  and deploys Stages in waves, with pre/post steps and manual approval. Source from GitLab through
  CodeConnections (`CodePipelineSource.connection`).
- When to use which, the ADR you will write: GitLab-native deploy keeps one tool and one audit trail for
  developers; CDK Pipelines keeps deploys inside AWS, self-updating, with cross-account waves built in.
  Both are reasonable; ask which one the team runs.

**Links:**
- [GitLab CI/CD](https://docs.gitlab.com/ci/)
- [CI/CD YAML reference](https://docs.gitlab.com/ci/yaml/)
- [Job rules](https://docs.gitlab.com/ci/jobs/job_rules/)
- [CI/CD variables](https://docs.gitlab.com/ci/variables/)
- [Merge request pipelines](https://docs.gitlab.com/ci/pipelines/merge_request_pipelines/)
- [Downstream pipelines](https://docs.gitlab.com/ci/pipelines/downstream_pipelines/)
- [CI/CD components](https://docs.gitlab.com/ci/components/)
- [Migrating from GitHub Actions](https://docs.gitlab.com/ci/migration/github_actions/)
- [OIDC to AWS](https://docs.gitlab.com/ci/cloud_services/aws/)
- [ID token authentication](https://docs.gitlab.com/ci/secrets/id_token_authentication/)
- [Environments](https://docs.gitlab.com/ci/environments/)
- [Protected environments](https://docs.gitlab.com/ci/environments/protected_environments/)
- [Deployment approvals](https://docs.gitlab.com/ci/environments/deployment_approvals/)
- [Build Docker images in GitLab CI](https://docs.gitlab.com/ci/docker/using_docker_build/)
- [Rootless Buildah in GitLab CI](https://docs.gitlab.com/ci/docker/buildah_rootless_tutorial/)
- [Container scanning](https://docs.gitlab.com/user/application_security/container_scanning/)
- [Secret detection](https://docs.gitlab.com/user/application_security/secret_detection/)
- [GitLab runners](https://docs.gitlab.com/ci/runners/)
- [Self-managed GitLab runners in CodeBuild](https://docs.aws.amazon.com/codebuild/latest/userguide/gitlab-runner.html)
- [CodeConnections: GitLab](https://docs.aws.amazon.com/dtconsole/latest/userguide/connections-create-gitlab.html)
- [CodePipeline GitLab connections](https://docs.aws.amazon.com/codepipeline/latest/userguide/connections-gitlab.html)
- [CDK Pipelines guide](https://docs.aws.amazon.com/cdk/v2/guide/cdk-pipeline.html)
- [CDK pipelines module](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.pipelines-readme.html)
- [CDK bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html)
- [Bootstrap environments (trust)](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping-env.html)
- [CDK stages](https://docs.aws.amazon.com/cdk/v2/guide/stages.html)
- [CDK assets](https://docs.aws.amazon.com/cdk/v2/guide/assets.html)
- [CDK aspects (policy checks at synth)](https://docs.aws.amazon.com/cdk/v2/guide/aspects.html)
- [CDK best practices](https://docs.aws.amazon.com/cdk/v2/guide/best-practices.html)

**Exercise:** On gitlab.com (free tier), build the portfolio pipeline: lint and test, `cdk synth` once,
ARM64 image build with container scanning, push to ECR in shared-services, `cdk diff` as an MR comment,
deploy to dev automatically, deploy to prod through a protected environment with one required approval.
OIDC only; show in the README that the project has no AWS keys. Add a CDK Aspect that fails synth if any
IAM policy has `*` actions. Then, on a branch, deploy the same Stages with CDK Pipelines sourced from
GitLab through CodeConnections, and write the one-page ADR comparing the two.

---

## 10. Systems Manager: Automation, Parameter Store, Session Manager

**Why:** "Configure and manage AWS Systems Manager (SSM) for operational automation" and "AWS Systems
Manager (SSM)" in the mandatory list.

**You already have:** years of operational automation in Jenkins, bash and Step Functions, and the
backup-before-mutate habit. SSM Automation is another place to encode it.

**Learn:**
- Automation runbooks: YAML documents with steps (`aws:executeAwsApi`, `aws:executeScript`,
  `aws:waitForAwsResourceProperty`, `aws:branch`, `aws:approve`), parameters, outputs, an assume role.
  The AWS-owned runbook library, and when to write your own.
- Running across accounts and regions from a central account; rate control and error thresholds.
- Approvals inside a runbook (`aws:approve`) and Change Manager for change requests with approvers.
- Parameter Store: standard vs advanced, SecureString with KMS, hierarchies per environment, versions and
  labels, when to use Secrets Manager instead (rotation). A good home for model IDs, prompt versions and
  feature flags that ops can change without a deploy.
- Session Manager: shell access without SSH or bastions, session logging to S3/CloudWatch, IAM-controlled.
  Mostly for any EC2 or ECS pieces; AgentCore Runtime has its own shell execution features.
- OpsCenter for operational work items from alarms.
- CDK: `aws-cdk-lib/aws-ssm` has L2s for parameters; Automation documents are `CfnDocument` (L1).

**Links:**
- [What is Systems Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/what-is-systems-manager.html)
- [Automation](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-automation.html)
- [Authoring runbooks](https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-authoring-runbooks.html)
- [Automation actions reference](https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-actions.html)
- [aws:executeScript](https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-action-executeScript.html)
- [aws:approve](https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-action-approve.html)
- [Running automations in multiple accounts and regions](https://docs.aws.amazon.com/systems-manager/latest/userguide/running-automations-multiple-accounts-regions.html)
- [AWS-owned runbook reference](https://docs.aws.amazon.com/systems-manager-automation-runbooks/latest/userguide/automation-runbook-reference.html)
- [Change Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/change-manager.html)
- [Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)
- [Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [OpsCenter](https://docs.aws.amazon.com/systems-manager/latest/userguide/OpsCenter.html)
- [CDK aws-ssm](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ssm-readme.html)

**Exercise:** Write three Automation runbooks for the portfolio, deployed with CDK:
1. **Roll back agent endpoint:** read the current `prod` endpoint version, save it to an S3 backup object,
   require `aws:approve`, point the endpoint at the previous version, then check the error-rate metric.
2. **Rotate OAuth client secret:** create the new secret at the IdP (mocked), update the credential
   provider, verify a token exchange succeeds, then retire the old secret.
3. **Drain:** set a Parameter Store flag the agent reads to refuse new sessions, wait until active
   sessions reach zero or a timeout, then report.
Run each once from the shared-services account against dev.

---

## 11. DynamoDB for agent state and session persistence

**Why:** "Design and optimize data persistence using Amazon DynamoDB" and "Amazon DynamoDB" in the
mandatory list. Role 4 section 8 covers DynamoDB for event-driven backends; this section is about what an
agent platform stores.

**Learn:**
- Decide what goes where: AgentCore Memory for conversation events and long-term memory records; Strands
  session storage for agent and orchestrator state; DynamoDB for the platform's own records (session
  index per user, conversation metadata, cost ledger, idempotency keys for tool side effects, approval
  state, feature flags per tenant). Know the line and defend it.
- Access-pattern-first modeling: write the queries first ("all sessions for user X in the last 7 days",
  "cost by agent by day", "has this tool call already run"), then pick keys and GSIs.
- Patterns: single-table with `PK`/`SK` prefixes, sparse GSIs, conditional writes for idempotency and
  optimistic locking, transactions, TTL to expire sessions, Streams to feed cost aggregation.
- Capacity: on-demand vs provisioned, hot partitions from one busy user or tenant.
- Security: leading-key IAM conditions per user or tenant, encryption with KMS, a gateway VPC endpoint.
- CDK: `TableV2` is the current L2 for new tables.

**Links:**
- [DynamoDB data modeling](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/data-modeling.html)
- [NoSQL design for DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html)
- [Condition expressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html)
- [Transactions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html)
- [Time to Live](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html)
- [DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html)
- [On-demand capacity mode](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/on-demand-capacity-mode.html)
- [Fine-grained access with IAM conditions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html)
- [CDK aws-dynamodb](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_dynamodb-readme.html)
- [AgentCore Memory](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)
- [Long-term memory vs RAG](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-ltm-rag.html)
- [Strands storage](https://strandsagents.com/docs/user-guide/sdk/storage/)

**Exercise:** Write down eight access patterns for the portfolio platform, then design one table with
keys and at most two GSIs that serves all eight. Implement: a session index item written on session
start with a 30-day TTL; an idempotency item written with `attribute_not_exists` before a tool performs
a side effect, so a retried tool call does not create a second access request; and a cost ledger fed by
a Stream-triggered Lambda that turns per-call token counts into a daily cost per agent. Show the retry
test and the cost query in the README.

---

## 12. Cost and performance optimization for agents

**Why:** "Optimize AI agent performance, scalability, and cost efficiency in production environments"
and "Monitor, troubleshoot, and optimize cloud workloads".

**You already have:** cost and quota work on AWS, and the habit of measuring before changing.

**Learn:**
- Where agent cost comes from: input tokens (system prompt plus tool schemas plus history, repeated every
  cycle), output tokens, number of loop cycles, multi-agent fan-out, Runtime session time, Gateway and
  Memory calls, logs and traces.
- Model choice: a smaller model for routing and simple specialists, a larger one only where quality needs
  it; Bedrock intelligent prompt routing; Strands model routing. Measure with an eval, not by feel.
- Prompt caching on Bedrock: cache checkpoints after the stable prefix (system prompt and tool
  definitions), minimum token counts per checkpoint, a TTL that resets on each hit (5 minutes for many
  models; check the model card). Strands exposes it through the Bedrock provider, and traces show cache
  read and write tokens.
- Token budgets: cap loop cycles and output tokens per turn, trim or summarize history, keep tool output
  small, semantic tool search instead of loading every tool schema.
- Inference options: on-demand, cross-Region inference profiles for throughput, application inference
  profiles for cost allocation tags per team or agent, service tiers (Reserved, Priority, Standard, Flex),
  batch inference for offline work. Quotas and throttling (ThrottlingException handling is in role 4
  section 1).
- Performance: cold start on Runtime, streaming responses, parallel tool calls, keeping the agent near
  its tools (region and VPC).
- Guardrails on spend: AWS Budgets alarms, per-conversation cost in the dashboard (section 7), Gateway rate
  limits per user.

**Links:**
- [Bedrock prompt caching](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html)
- [Strands: Bedrock prompt caching](https://strandsagents.com/docs/user-guide/sdk/model-providers/amazon-bedrock-prompt-caching/)
- [Bedrock intelligent prompt routing](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-routing.html)
- [Inference profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html)
- [Create an application inference profile](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-create.html)
- [Service tiers](https://docs.aws.amazon.com/bedrock/latest/userguide/service-tiers-inference.html)
- [Batch inference](https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference.html)
- [Bedrock quotas](https://docs.aws.amazon.com/bedrock/latest/userguide/quotas.html)
- [Model cards](https://docs.aws.amazon.com/bedrock/latest/userguide/model-cards.html)
- [Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)
- [AgentCore pricing](https://aws.amazon.com/bedrock/agentcore/pricing/)
- [AgentCore quotas](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/bedrock-agentcore-limits.html)
- [Gateway rate limits](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-rate-limits.html)
- [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)
- [Well-Architected Generative AI Lens](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/generative-ai-lens.html)

**Exercise:** Take a fixed set of 30 conversations and record a baseline: tokens, cache hits, cycles,
p50/p95 latency, cost per conversation and an eval score. Then change one thing at a time: enable prompt
caching on the system prompt and tool schemas; move the router to a smaller model; cap cycles at 6; turn
on semantic tool search. Put the before/after table in the README, including any change that hurt quality
and was rolled back.

---

## 13. Certifications and how to present the background

**Why:** Preferred: "AWS Certified Solutions Architect / AWS DevOps Engineer Certification." For a
contract role, a current cert also helps a resume through keyword screens.

**Learn:**
- Current names (checked on the certification pages): **AWS Certified Solutions Architect - Professional**
  (the exam guide is now version 03, SAP-C03) and **AWS Certified DevOps Engineer - Professional**
  (DOP-C02). Both are 180 minutes, 75 questions. Check the exam guide before you study; versions change.
- Pick DevOps Engineer - Professional first. It matches the "primary focus" of the posting (CI/CD, IaC,
  monitoring, incident response, multi-account) and the work you already do, so it is the fastest
  credible win. Solutions Architect - Professional second if the contract wants "architect" on paper.
- AWS Certified Generative AI Developer - Professional exists and covers Bedrock and agents. It is not
  named in this posting; consider it later if you target more AI-heavy roles.
- Resume framing: lead with the mandatory block in the posting's own words (multi-account AWS, CDK and
  pipelines, IAM and federation, CloudWatch and CloudTrail, release management, P1s). Then one line for
  the portfolio: "Built an enterprise agent platform on AgentCore, Strands, MCP and Cedar (public repo)",
  with the link. Say plainly that the agentic work is a personal build, not a client system.

**Links:**
- [AWS Certified Solutions Architect - Professional](https://aws.amazon.com/certification/certified-solutions-architect-professional/)
- [SAP-C03 exam guide](https://docs.aws.amazon.com/aws-certification/latest/solutions-architect-professional-03/solutions-architect-professional-03.html)
- [AWS Certified DevOps Engineer - Professional](https://aws.amazon.com/certification/certified-devops-engineer-professional/)
- [DOP-C02 exam guide](https://docs.aws.amazon.com/aws-certification/latest/devops-engineer-professional-02/devops-engineer-professional-02.html)
- [AWS Certified Generative AI Developer - Professional](https://aws.amazon.com/certification/certified-generative-ai-developer-professional/)
- [AWS Skill Builder](https://skillbuilder.aws/)

**Exercise:** Book DevOps Engineer - Professional in week 1. Rewrite the top third of your resume for this
posting: six bullets that each match a "Mandatory & Critical" item with a concrete result, then the
portfolio line. Prepare a 5-minute walkthrough of the portfolio architecture that starts at the org
layout and ends at the cost-per-conversation panel.
