# Role 4: FDE/SME - AWS Cloud Engineer with Agentic AI: highlights

The posting is in [posting.md](posting.md). The full material list with links is in [details.md](details.md).
Do the [shared core](../../shared/highlights.md) first. This track assumes you have it and only adds what is
specific to AWS: Bedrock, AgentCore, retrieval and graphs on AWS, multi-tenant identity, and AWS Quick Sight
(formerly Amazon QuickSight) embedded analytics.

## Where you start

| Posting asks for | You already have |
|---|---|
| SME level knowledge of AWS cloud | Deep hands-on AWS: CDK in TypeScript, EKS, Lambda, Step Functions, CodeBuild, Firehose, S3 Tables, SNS, CloudWatch, the Support API |
| IAM, federation, least privilege | IAM users and roles, SAML federation, EKS access entries, cross-account work, least-privilege reviews |
| Rapid diagnosis, hands-on debugging | 26 years of P1s across AWS, Azure, Kubernetes, Jenkins, AD/LDAP/Kerberos, Linux and Windows |
| Converting one-off fixes into reusable patterns | Runbooks, CLAUDE.md rules, skills and hooks written after real incidents |
| Lambda, SDK, event-driven integration, error handling | Lambda and Step Functions in production, boto3 scripts, CDK constructs, SNS/CloudWatch alerting |
| Hands on with vibe coding and AI tools | A daily Claude Code harness: rules, skills, hooks, MCP servers (Jira, Spacelift, AWS), permission modes |
| Excellent communication | Incident write-ups, tickets, change records, explaining infra to app teams |

What you do not have yet, said plainly: a production Bedrock or AgentCore solution, RAG and vector stores
in practice, knowledge graphs and Neptune, Cognito and multi-tenant SaaS identity, Quick Sight and embedded
analytics, and DynamoDB data modeling beyond basic use.

## Honest fit note

The posting says "must have created at least one production level solution using amazon bedrock and
agentcore". That is a hard gate, and today you probably do not meet it. Do not claim it. FDE interviews are
live and hands-on, and a claimed production build gets probed down to error codes and quota numbers.

What it takes to close it:

1. **Best option: ship one at work.** Find a small internal use case where an agent on Bedrock and AgentCore
   is useful and low risk, for example a read-only ops assistant over runbooks and ticket history. Get it
   approved, deploy it with IaC, real users, auth, logging and an owner. Even a narrow internal tool with
   a handful of users is "production level" if it is deployed, monitored and supported.
2. **Fallback: a production-grade public build.** The portfolio project below, deployed and kept running,
   with CDK, auth, guardrails, alarms, evals and a cost budget. Describe it exactly as what it is: "a
   production-grade deployment I run, not a customer system". Ask the recruiter early whether that
   satisfies the requirement. Some clients accept it and some do not; it is better to know before the
   interview loop.
3. **Either way:** be able to explain every decision in the build: model choice, why AgentCore Runtime
   over Lambda, how sessions are isolated, how tenant identity reaches the tools, what you log, what it
   costs per request, and what broke on the way.

The rest of the posting fits you well. The AWS depth, the identity background and the diagnosis
experience are the hard parts of an FDE job, and you have those. The new services can be learned in weeks.

## Gaps, most important first

1. **Bedrock and AgentCore, built and deployed.** Hard gate in the posting. Converse API, tool use, Guardrails,
   then AgentCore Runtime, Gateway, Memory, Identity and Observability in one deployed agent.
2. **RAG and vector stores on AWS.** "Must have clear understanding". Bedrock Knowledge Bases, chunking,
   metadata filtering, and the trade-offs between OpenSearch Serverless, S3 Vectors and Aurora pgvector.
3. **Knowledge graphs and Neptune.** Also "must have". Graph modeling, openCypher, Neptune vs Neptune
   Analytics, and GraphRAG through Bedrock Knowledge Bases.
4. **Multi-tenant identity.** Cognito user pools, federation, tenant claims in tokens, tenant-to-user mapping,
   and enforcing tenant boundaries in tools and data, not in the prompt. Your IAM depth makes this the
   fastest gap to close.
5. **Quick Sight and embedded analytics.** A full skill line each in the posting, and new to you: SPICE, RLS,
   asset promotion, GenerateEmbedUrl APIs, the Embedding SDK, allowed domains, session lifecycle.
6. **DynamoDB data modeling.** Access-pattern-first design, partition keys for tenants, conditional writes,
   streams. It is in the skill matrix.
7. **FDE framing.** You have the skill. Practice telling it as customer stories: ambiguous ask, fast
   diagnosis, fix, then the reusable pattern that came out of it.

## Six-week plan (after the shared core)

| Week | Focus | Output |
|---|---|---|
| 1 | Bedrock: Converse API, tool use, Guardrails, prompt caching, invocation logging, quotas | A TypeScript or boto3 script that runs a tool-calling loop on Bedrock with a guardrail attached, plus token and cost logging |
| 2 | AgentCore: Runtime, Gateway, Memory, Identity, Observability, AgentCore CLI and the stable CDK constructs | The week-1 agent deployed on AgentCore Runtime, tools behind Gateway, traces visible in CloudWatch |
| 3 | RAG on AWS: Knowledge Bases, chunking, metadata filters, S3 Vectors vs OpenSearch Serverless vs Aurora pgvector, retrieval evals | A Knowledge Base over synthetic tenant documents, a 20-question retrieval eval, a one-page store comparison |
| 4 | Identity: Cognito user pools, federation, pre token generation trigger, JWT authorizers, tenant isolation; DynamoDB modeling | Cognito users mapped to tenants, a tenant claim flowing from the token into every tool call, a DynamoDB table keyed by tenant |
| 5 | Knowledge graphs: Neptune Analytics, openCypher, GraphRAG in Knowledge Bases | A small entity graph per tenant and a graph tool the agent can call |
| 6 | Quick Sight: datasets, SPICE, RLS, asset bundles, registered and anonymous embedding | An embedded dashboard with per-tenant RLS, promoted dev to prod with asset bundle export/import; the portfolio project finished |

Weeks 1 to 6 all feed the same project, so by the end you have one deployed system rather than six demos.

## Portfolio project: multi-tenant "ask your data" on AWS

A small SaaS-shaped app where users from two or three fictional tenants ask questions about their own data
and get answers, citations and a dashboard. Public repo, synthetic data, all infrastructure in CDK.

- **Agent:** a Strands or similar agent on AgentCore Runtime, calling Bedrock through the Converse API with a
  Guardrail attached. Short-term and long-term memory in AgentCore Memory, namespaced per tenant and user.
- **Tools:** exposed through AgentCore Gateway as MCP tools backed by Lambda: document search (Bedrock
  Knowledge Base with a tenant metadata filter), entity relationships (Neptune Analytics, openCypher), and
  structured lookups (DynamoDB, tenant as partition key).
- **Identity:** Cognito user pool, one app client, a `tenant_id` claim added by a pre token generation
  trigger. AgentCore Identity validates the inbound JWT. Every tool derives the tenant from the verified
  token, never from the prompt or a tool argument, and the IAM role on each Lambda is scoped by tag or prefix.
- **Analytics:** a Quick Sight dashboard embedded with GenerateEmbedUrlForRegisteredUser (or anonymous with
  session tags), RLS per tenant, allowed domains set, assets promoted from dev to prod with asset bundles.
- **Proof, not claims:** a cross-tenant test suite that tries to read another tenant's data through every
  path (prompt injection in a document, a forged tool argument, a tampered dashboard URL) and shows each one
  fail. A retrieval eval, a cost-per-question number, and CloudWatch traces. Reuse the
  [shared evals](../../shared/details.md#5-verification-and-evals) and
  [LLM security](../../shared/details.md#6-llm-security) work.
- **Write-up:** a README that reads like an FDE engagement report: the ask, the architecture, the three
  hardest bugs, and the reusable CDK construct you extracted at the end.

## Skill matrix (the posting asks for it)

Fill in years yourself. Ratings must be honest: FDE interviews probe every number live, often by having you
build or debug on the spot, so a 4 that turns out to be a 2 costs more than writing 2.

| Skill | Years of experience | Honest starting point (1-5) | Target after this track (1-5) |
|---|---|---|---|
| FDE | | 3: deep diagnosis and hands-on debugging with internal teams; not a formal customer-facing FDE role | 3-4, with prepared customer-style stories |
| AWS | | 4: deep infra and serverless; weaker on app-facing services like Cognito, Quick Sight, DynamoDB modeling | 4-5 |
| Lambda | | 4: production use with CDK, SNS, Step Functions | 4 |
| Agentic AI | | 3: heavy daily use and a self-built agent harness; no deployed agent product yet | 4, with the portfolio project or a work build |
| Bedrock | | 1: not used in production | 3 |
| RAG | | 1-2: concepts only | 3 |
| Vector DB | | 1: not used | 2-3 |
| Vibe coding | | 4: daily Claude Code with rules, skills, hooks, MCP | 4-5 |
| SDK | | 3: CDK in TypeScript, boto3 scripts | 4 |
| DynamoDB | | 2: basic use, no deep data modeling | 3 |

## One-line pitch

"I have spent 26 years debugging AWS and enterprise systems with the people who own them; I build agents
on Bedrock and AgentCore with the same rules I use for production: identity enforced in code, tenants
isolated by design, and every claim backed by a test."

Use the second half only once the Bedrock and AgentCore build actually exists.
