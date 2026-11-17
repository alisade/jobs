# Role 4: FDE/SME - AWS Cloud Engineer with Agentic AI: details

Material for each item in [highlights.md](highlights.md). Every topic has the same parts: why it matters,
what to learn, links, and an exercise. All links were checked on 2026-11-13.

Shared topics are not repeated here. For agent patterns see
[shared section 2](../../shared/details.md#2-agent-design-patterns-and-context-engineering), for tool calling
[shared section 3](../../shared/details.md#3-tool-calling-and-structured-outputs), for MCP
[shared section 4](../../shared/details.md#4-mcp-model-context-protocol), for evals
[shared section 5](../../shared/details.md#5-verification-and-evals) and for prompt injection
[shared section 6](../../shared/details.md#6-llm-security).

Naming note: Amazon QuickSight is now AWS Quick Sight, the BI feature inside AWS Quick. The docs say all
existing QuickSight APIs and SDKs keep working, so API names still say `quicksight`.

---

## 1. Amazon Bedrock: Converse API, tools, Guardrails

**Why:** "must have created at least one production level solution using amazon bedrock and agentcore".
Bedrock is the model layer under everything else in this track.

**You already have:** IAM, quotas, CloudWatch and CDK, which cover most of what makes a Bedrock app
production-ready rather than a demo.

**Learn:**
- Converse API vs InvokeModel: one request shape across models, tool use, streaming with ConverseStream
- Tool use on Bedrock: `toolConfig`, `toolUse` and `toolResult` blocks, and the loop you write around them
- Model access, inference profiles and cross-Region inference, and what they mean for quotas and data residency
- Guardrails: content filters, denied topics, PII redaction, contextual grounding check; attaching a guardrail to Converse
- Prompt caching, model invocation logging, token and cost tracking
- Errors you will be asked about: ThrottlingException, AccessDeniedException on model access, ValidationException on bad tool schemas

**Links:**
- [What is Amazon Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)
- [Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html)
- [Tool use with Converse](https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use.html)
- [Cross-Region inference](https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html)
- [Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html)
- [Use a guardrail with the Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-use-converse-api.html)
- [Contextual grounding check](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-contextual-grounding-check.html)
- [Prompt caching](https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html)
- [Model invocation logging](https://docs.aws.amazon.com/bedrock/latest/userguide/model-invocation-logging.html)
- [boto3 converse reference](https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/converse.html)
- [AWS SDK for JavaScript v3](https://docs.aws.amazon.com/sdk-for-javascript/v3/developer-guide/welcome.html)
- [Amazon Bedrock workshop (GitHub)](https://github.com/aws-samples/amazon-bedrock-workshop)
- [CDK Bedrock construct library](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_bedrock-readme.html)

**Exercise:** In TypeScript, write a Converse loop with two tools (a DynamoDB lookup and a fake "create
ticket" tool). Attach a guardrail that blocks one denied topic and redacts email addresses. Log input
tokens, output tokens and estimated cost per request. Then trigger a ThrottlingException on purpose and
add retry with backoff and jitter.

---

## 2. Amazon Bedrock AgentCore

**Why:** the same hard gate: "production level solution using amazon bedrock and agentcore". AgentCore is
how AWS expects agents to run in production, and an FDE will be asked to deploy and debug it with a customer.

**You already have:** containers, IAM roles, OAuth/SAML concepts and CloudWatch, which map directly onto
Runtime, Identity and Observability.

**Learn:**
- Runtime: hosting any framework (Strands, LangGraph, your own), session isolation in microVMs, session lifetime, inbound auth with IAM SigV4 or JWT
- Gateway: turning Lambda functions and OpenAPI specs into MCP tools, inbound auth, outbound credentials, tool search
- Memory: short-term events vs long-term records, memory strategies (semantic, summary, user preference), namespaces per user or tenant
- Identity: workload identity for the agent, inbound JWT validation, outbound OAuth and API keys from the token vault, acting on behalf of a user
- Observability: OpenTelemetry traces and spans in CloudWatch, what to put on a dashboard, audit logging
- Policy (Cedar rules on tool calls) and Evaluations: know what they are and when you would add them
- Tooling: the AgentCore CLI (the older starter toolkit is marked deprecated) and the CDK constructs, now stable in `aws-cdk-lib/aws-bedrockagentcore`, Policy included as of aws-cdk-lib 2.277
- When Runtime is the right answer and when a plain Lambda with Converse is enough

**Links:**
- [What is AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html)
- [AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html)
- [Runtime: how it works (microVMs)](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-how-it-works.html)
- [Runtime sessions](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-sessions.html)
- [Runtime inbound and outbound auth](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-oauth.html)
- [AgentCore Gateway](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html)
- [Gateway inbound authorization](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-inbound-auth.html)
- [AgentCore Memory](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)
- [Memory strategies](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-strategies.html)
- [AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html)
- [AgentCore Observability](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability.html)
- [AgentCore Policy](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html)
- [AgentCore Evaluations](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/evaluations.html)
- [AgentCore CLI (GitHub)](https://github.com/aws/agentcore-cli)
- [AgentCore samples (GitHub)](https://github.com/awslabs/agentcore-samples)
- [CDK aws-bedrockagentcore module (stable)](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_bedrockagentcore-readme.html)
- [Strands Agents](https://strandsagents.com/latest/)
- [AWS Well-Architected Generative AI Lens](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/generative-ai-lens.html)

**Exercise:** Deploy the section 1 agent to AgentCore Runtime with CDK. Move its tools behind Gateway as
Lambda targets. Require a Cognito JWT for inbound calls. Add Memory with a per-user namespace and show that
user B cannot recall user A's facts. Open the trace for one request in CloudWatch and explain each span.
Write down cold start, p50 latency and cost per session.

---

## 3. RAG and vector stores on AWS

**Why:** "Must have clear understanding of RAG, vector db". RAG and Vector DB both have their own row in
the skill matrix.

**Learn:**
- Bedrock Knowledge Bases: data sources, ingestion and sync, Retrieve vs RetrieveAndGenerate, citations
- Chunking: fixed, hierarchical, semantic; how chunk size changes answer quality and cost
- Metadata and filters: attaching `tenant_id` to every document and filtering on it at query time
- Vector stores and when to pick each:
  - OpenSearch Serverless: hybrid keyword plus vector search, higher baseline cost
  - S3 Vectors: low cost at large scale, simpler query features
  - Aurora PostgreSQL with pgvector: when the data already lives in Postgres and you want SQL joins
- Evaluating retrieval separately from generation: recall at k, groundedness, Bedrock RAG evaluations
- Contextual retrieval and reranking (see the [shared RAG note](../../shared/details.md#retrieval-rag-light-coverage))

**Links:**
- [Bedrock Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [Supported models and Regions for Knowledge Bases](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-supported.html)
- [Using your own vector store](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-setup.html)
- [Chunking](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-chunking.html)
- [Metadata in a data source](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-metadata.html)
- [Query a knowledge base](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-test-retrieve.html)
- [Configure queries and response generation](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-test-config.html)
- [Evaluate RAG sources](https://docs.aws.amazon.com/bedrock/latest/userguide/evaluation-kb.html)
- [Multi-tenancy in a single Knowledge Base with metadata filtering (AWS blog)](https://aws.amazon.com/blogs/machine-learning/multi-tenancy-in-rag-applications-in-a-single-amazon-bedrock-knowledge-base-with-metadata-filtering/)
- [OpenSearch Serverless vector search](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-vector-search.html)
- [S3 Vectors](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors.html)
- [S3 Vectors with Bedrock Knowledge Bases](https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-vectors-bedrock-kb.html)
- [Aurora PostgreSQL as a Knowledge Base store](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.VectorDB.html)
- [Generative AI CDK Constructs (GitHub)](https://github.com/awslabs/generative-ai-cdk-constructs)

**Exercise:** Build one Knowledge Base over 50 synthetic documents for three tenants, with `tenant_id`
metadata, on S3 Vectors. Write 20 questions with known source documents and measure recall at 5 for two
chunking strategies. Then write a one-page comparison of S3 Vectors, OpenSearch Serverless and Aurora
pgvector for a customer who asks "which one should we use", including cost drivers.

---

## 4. Knowledge graphs and Amazon Neptune

**Why:** "Must have clear understanding of RAG, vector db, knowledge graphs, Amazon neptune". Graphs answer
relationship questions ("which vendors supply parts used by these three products") that vector search
handles badly.

**You already have:** LDAP and AD, which are directory graphs: you already think in nodes, edges and
traversals.

**Learn:**
- Property graphs vs RDF; nodes, edges, labels and properties; modeling a domain as a graph
- openCypher basics: MATCH, WHERE, path patterns, variable-length paths
- Neptune Database (transactional, clusters) vs Neptune Analytics (in-memory, analytics algorithms, vector similarity)
- GraphRAG: entity extraction during ingestion, then retrieval that follows graph links as well as vector similarity; Bedrock Knowledge Bases can build this on Neptune Analytics
- IAM authentication for Neptune and VPC placement
- When a graph is overkill and a DynamoDB adjacency list or SQL join is enough

**Links:**
- [What is Amazon Neptune](https://docs.aws.amazon.com/neptune/latest/userguide/intro.html)
- [What is Neptune Analytics](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/what-is-neptune-analytics.html)
- [Vector similarity in Neptune Analytics](https://docs.aws.amazon.com/neptune-analytics/latest/userguide/vector-similarity.html)
- [openCypher on Neptune](https://docs.aws.amazon.com/neptune/latest/userguide/access-graph-opencypher.html)
- [Neptune IAM authentication](https://docs.aws.amazon.com/neptune/latest/userguide/iam-auth.html)
- [Build a Knowledge Base with Neptune Analytics graphs](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-build-graphs.html)
- [Build GraphRAG applications using Bedrock Knowledge Bases (AWS blog)](https://aws.amazon.com/blogs/machine-learning/build-graphrag-applications-using-amazon-bedrock-knowledge-bases/)
- [GraphRAG toolkit (awslabs, GitHub)](https://github.com/awslabs/graphrag-toolkit)

**Exercise:** Model a small supply chain (suppliers, parts, products, customers) for two tenants in Neptune
Analytics. Write five openCypher queries, two of them multi-hop. Wrap one as an agent tool that always
adds the caller's tenant to the MATCH clause. Then build a GraphRAG Knowledge Base over the same documents
and compare its answers to plain vector RAG on five relationship questions.

---

## 5. Multi-tenant identity and authorization boundaries

**Why:** "IAM, Cognito/federation, application identity, tenant-to-user mapping, authorization boundaries,
least privilege".

**You already have:** IAM users and roles, SAML federation, EKS access entries, cross-account access and
least-privilege practice. The new part is application identity: users in an app, not operators in an
account.

**Learn:**
- Cognito user pools vs identity pools; app clients, scopes, groups
- Federation: SAML and OIDC identity providers into a user pool, one IdP per tenant
- Tenant-to-user mapping: a `tenant_id` claim from a custom attribute or the pre token generation trigger
- Multi-tenant models in Cognito: one pool with attributes, groups per tenant, app client per tenant, pool per tenant; trade-offs
- API Gateway JWT and Cognito authorizers; passing verified claims downstream
- Enforcing tenant isolation below the app: IAM session tags and ABAC, DynamoDB leading-key conditions, per-tenant prefixes in S3
- The agent rule: the tool takes the tenant from the verified token, never from the model's arguments
- Amazon Verified Permissions (Cedar) for fine-grained app authorization

**Links:**
- [What is Amazon Cognito](https://docs.aws.amazon.com/cognito/latest/developerguide/what-is-amazon-cognito.html)
- [User pool federation with third-party IdPs](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-identity-federation.html)
- [Building B2B multi-tenant applications with Cognito](https://docs.aws.amazon.com/cognito/latest/developerguide/multi-tenant-application-best-practices.html)
- [Pre token generation trigger](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html)
- [Identity pools role-based access control](https://docs.aws.amazon.com/cognito/latest/developerguide/role-based-access-control.html)
- [HTTP API JWT authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html)
- [REST API Cognito authorizer](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html)
- [STS session tags](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_session-tags.html)
- [Controlling access with tags (ABAC)](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_tags.html)
- [DynamoDB fine-grained access with IAM conditions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/specifying-conditions.html)
- [Amazon Verified Permissions](https://docs.aws.amazon.com/verifiedpermissions/latest/userguide/what-is-avp.html)
- [SaaS Lens (Well-Architected)](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html)
- [CDK Cognito construct library](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito-readme.html)

**Exercise:** In CDK, build a user pool with two tenants and a pre token generation trigger that adds
`tenant_id`. Put an HTTP API with a JWT authorizer in front of a Lambda that reads DynamoDB. Make the Lambda
assume a role with a `tenant_id` session tag, and give that role a policy with
`dynamodb:LeadingKeys` matching the tag. Write a test where tenant A's token tries to read tenant B's item
three ways (forged path parameter, forged body, prompt-injected tool argument) and show all three fail at
IAM, not in app code.

---

## 6. AWS Quick Sight analytics

**Why:** "Datasets, SPICE, calculated fields, parameters, filters, RLS, permissions, dashboards, analyses,
APIs, asset promotion".

**Learn:**
- Data sources, datasets, analyses and dashboards, and how they depend on each other
- SPICE: import vs direct query, capacity, scheduled and API-driven refresh, ingestion errors
- Calculated fields, parameters, filters and controls
- Row-level security: user-based rules datasets vs tag-based rules (used with anonymous embedding)
- Permissions: users, groups, namespaces (one per tenant is a common multi-tenant pattern), asset sharing
- APIs: everything in the console is also an API, which is how you automate it
- Asset promotion: asset bundle export and import jobs to move dashboards from dev to prod, with parameter overrides for data source ARNs; CDK and CloudFormation support

**Links:**
- [What is AWS Quick](https://docs.aws.amazon.com/quick/latest/userguide/what-is.html)
- [Working with datasets](https://docs.aws.amazon.com/quick/latest/userguide/working-with-datasets.html)
- [Importing data into SPICE](https://docs.aws.amazon.com/quick/latest/userguide/spice.html)
- [Refreshing SPICE data](https://docs.aws.amazon.com/quick/latest/userguide/refreshing-imported-data.html)
- [Adding calculations](https://docs.aws.amazon.com/quick/latest/userguide/working-with-calculated-fields.html)
- [Parameters](https://docs.aws.amazon.com/quick/latest/userguide/parameters-in-quicksight.html)
- [Row-level security overview](https://docs.aws.amazon.com/quick/latest/userguide/row-level-security.html)
- [RLS with user-based rules](https://docs.aws.amazon.com/quick/latest/userguide/restrict-access-to-a-data-set-using-row-level-security.html)
- [RLS with tag-based rules](https://docs.aws.amazon.com/quick/latest/userguide/quicksight-dev-rls-tags.html)
- [Quick Sight API reference](https://docs.aws.amazon.com/quicksight/latest/APIReference/)
- [Asset bundle operations](https://docs.aws.amazon.com/quicksight/latest/developerguide/asset-bundle-ops.html)
- [StartAssetBundleExportJob](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_StartAssetBundleExportJob.html)
- [CDK QuickSight construct library](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_quicksight-readme.html)

**Exercise:** Load a synthetic sales table for three tenants into SPICE from S3 or Athena. Build an analysis
with two calculated fields, one parameter-driven filter and a published dashboard. Add a user-based RLS
rules dataset keyed on tenant. Then export the dashboard with an asset bundle job, import it into a second
"prod" account or namespace with a different data source, and script the whole promotion in boto3.

---

## 7. Embedded analytics engineering

**Why:** "Registered/anonymous embedding, GenerateEmbedUrl APIs, QuickSight Embedding SDK, session
lifecycle, allowed domains, dashboard permissions".

**Learn:**
- Registered user embedding (`GenerateEmbedUrlForRegisteredUser`): the user exists in Quick Sight, permissions and user-based RLS apply
- Anonymous embedding (`GenerateEmbedUrlForAnonymousUser`): no Quick Sight user, session tags drive tag-based RLS, capacity pricing
- The embed URL is short-lived and single-use; the session it opens has its own lifetime; your backend must mint a fresh URL per page load
- Allowed domains: the `AllowedDomains` parameter on the call vs domains allowed at the account level
- The Embedding SDK: embedding a dashboard, visual or console; events, parameters and runtime filters from the host page
- Where the backend fits: a Lambda behind API Gateway that verifies the Cognito JWT, maps the user to a tenant and calls GenerateEmbedUrl with that tenant's session tags
- Common failures: domain not allowed, expired URL, user not found in the namespace, missing dashboard permission, RLS returning no rows

**Links:**
- [Embedded analytics overview](https://docs.aws.amazon.com/quick/latest/userguide/embedded-analytics.html)
- [Embedding Quick Sight into your applications](https://docs.aws.amazon.com/quick/latest/userguide/embedding-overview.html)
- [Developer guide: embed assets](https://docs.aws.amazon.com/quicksight/latest/developerguide/embedded-analytics.html)
- [Choose the right embedding solution](https://docs.aws.amazon.com/quicksight/latest/developerguide/embedded-analytics-choosing-right-solution.html)
- [Create your first embedding application](https://docs.aws.amazon.com/quicksight/latest/developerguide/embedded-analytics-first-app.html)
- [Embedding security](https://docs.aws.amazon.com/quicksight/latest/developerguide/embedded-analytics-security.html)
- [GenerateEmbedUrlForRegisteredUser](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_GenerateEmbedUrlForRegisteredUser.html)
- [GenerateEmbedUrlForAnonymousUser](https://docs.aws.amazon.com/quicksight/latest/APIReference/API_GenerateEmbedUrlForAnonymousUser.html)
- [Managing domains](https://docs.aws.amazon.com/quick/latest/userguide/manage-domains.html)
- [Runtime filtering for embedded dashboards](https://docs.aws.amazon.com/quick/latest/userguide/embedding-runtime-filtering.html)
- [Quick Sight Embedding SDK (GitHub)](https://github.com/awslabs/amazon-quicksight-embedding-sdk)

**Exercise:** Embed the section 6 dashboard in a small web page served from S3 and CloudFront. Build the
backend Lambda twice: once with registered embedding and user-based RLS, once with anonymous embedding and
tag-based RLS from the tenant claim. Break it on purpose four ways (wrong domain, reused URL, missing
permission, wrong tag) and write down the exact error each one produces. That list is what a customer
debugging session sounds like.

---

## 8. Lambda, API Gateway and DynamoDB event-driven backends

**Why:** "Lambda, API Gateway, SDK/Boto3, S3, DynamoDB, event-driven integration, error handling".
Lambda, SDK and DynamoDB are also rows in the skill matrix.

**You already have:** production Lambda, Step Functions, SNS, Firehose and CDK. Focus on DynamoDB modeling
and on error handling patterns you can explain on a whiteboard.

**Learn:**
- DynamoDB: design from access patterns, partition and sort keys, single-table vs multi-table, GSIs, tenant as the leading key
- Conditional writes, transactions, TTL, and DynamoDB Streams into Lambda
- Invocation models: sync, async, event source mapping; retries, DLQs and on-failure destinations for each
- SQS with Lambda: batch size, partial batch failure, visibility timeout, poison messages
- Idempotency: why retries make it mandatory, and Powertools idempotency
- Timeouts, retries and backoff with jitter; throttling and reserved concurrency
- EventBridge for fan-out between services
- Powertools for logging, tracing and metrics in TypeScript and Python

**Links:**
- [What is AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [Lambda retry behavior](https://docs.aws.amazon.com/lambda/latest/dg/invocation-retries.html)
- [Async invocation destinations and DLQs](https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-retain-records.html)
- [Lambda with SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)
- [What is EventBridge](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html)
- [DynamoDB data modeling](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/data-modeling.html)
- [NoSQL design for DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html)
- [Partition key design](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html)
- [DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html)
- [The what, why and when of single-table design (Alex DeBrie)](https://www.alexdebrie.com/posts/dynamodb-single-table/)
- [Powertools for AWS Lambda (TypeScript)](https://docs.aws.amazon.com/powertools/typescript/latest/)
- [Powertools idempotency (Python)](https://docs.aws.amazon.com/powertools/python/latest/utilities/idempotency/)
- [Timeouts, retries and backoff with jitter (Builders Library)](https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter)
- [Serverless Land patterns](https://serverlessland.com/patterns)

**Exercise:** Model a document-ingestion pipeline for the portfolio app in one DynamoDB table: tenants,
documents, ingestion jobs and job status, with every access pattern written down first. An S3 upload goes
through EventBridge to SQS to a Lambda that starts a Knowledge Base sync and records status with a
conditional write. Make the Lambda idempotent, add partial batch failure handling and a DLQ, then replay
the same event three times and show one job record.

---

## 9. FDE skills: diagnosis with the customer, then reusable patterns

**Why:** "Rapid diagnosis, working against ambiguous requirements, hands-on debugging with the customer,
converting one-off fixes into reusable patterns".

**You already have:** this is your 26 years. P1s, unfamiliar systems, people who describe the symptom and
not the cause, and fixes that became runbooks, hooks and skills.

**Learn:**
- Turning an ambiguous ask into a scoped first delivery: restate the problem, name the user, define "working", agree what is out of scope
- Diagnosing in front of a customer: say your hypothesis out loud, check the cheapest signal first, narrate what each result rules out
- Agent-specific triage order: auth and model access, quotas and throttling, tool errors, retrieval misses, then prompt and model behavior
- Leaving something behind: a CDK construct, a runbook, a test, an eval case for the bug that just happened
- Telling it as a story: situation, what was ambiguous, how you narrowed it, the fix, the reusable pattern
- Cost and latency conversations: how to give a customer a per-request cost estimate they can budget on

**Links:**
- [AWS Well-Architected Generative AI Lens](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/generative-ai-lens.html)
- [SaaS Lens (Well-Architected)](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html)
- [Builders Library](https://builder.aws.com/learn/topics/builders-library)
- [AWS Certified Generative AI Developer - Professional](https://aws.amazon.com/certification/certified-generative-ai-developer-professional/)
- [AWS Skill Builder](https://skillbuilder.aws/)

**Exercise:** Write five FDE stories from your own history, each under 200 words, in the format above.
At least two should end with a reusable artifact. Then ask a friend to play a customer with a vague
complaint about the portfolio app ("the bot gives wrong answers for some users") and run a 30-minute
live debugging session out loud. Record what you checked, in what order, and what you would turn into a
permanent test.
