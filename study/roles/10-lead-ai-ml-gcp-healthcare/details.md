# Role 10: Lead / Senior AI/ML Engineer with GCP (healthcare payer): details

Links checked on 2026-11-13. Material for each item in [highlights.md](highlights.md). Every topic has the
same parts: why it matters, what you already have (only where true), what to learn, links, and an exercise.

Topics covered elsewhere are linked, not repeated: agent patterns
([shared section 2](../../shared/details.md#2-agent-design-patterns-and-context-engineering)), tool calling
and structured outputs ([shared section 3](../../shared/details.md#3-tool-calling-and-structured-outputs)),
MCP ([shared section 4](../../shared/details.md#4-mcp-model-context-protocol)), eval method
([shared section 5](../../shared/details.md#5-verification-and-evals)), LLM security
([shared section 6](../../shared/details.md#6-llm-security)), Gemini on Vertex AI in production
([role 5 section 4](../05-java-fullstack-ai-gemini/details.md#4-gemini-on-vertex-ai-in-production)), RAG
Engine and Agent Search ([role 5 section 7](../05-java-fullstack-ai-gemini/details.md#7-rag-on-gcp)),
FastAPI on Cloud Run ([role 5 section 8](../05-java-fullstack-ai-gemini/details.md#8-python-fastapi-services-on-cloud-run)),
supervised tuning of Gemini ([role 5 section 9](../05-java-fullstack-ai-gemini/details.md#9-fine-tuning-on-vertex-ai-supervised-tuning-of-gemini)),
the Gen AI evaluation service ([role 5 section 10](../05-java-fullstack-ai-gemini/details.md#10-evaluation-on-gcp-gen-ai-evaluation-service-and-agent-evals)),
and GCP foundations, Terraform and IAM ([role 6 sections 1, 3 and 7](../06-platform-engineer-gcp-terraform/details.md#1-gcp-fundamentals-mapped-from-aws)).

**Naming note.** Google moved the Vertex AI docs under "Gemini Enterprise Agent Platform"
(`docs.cloud.google.com/gemini-enterprise-agent-platform/...`). Old `vertex-ai/...` URLs redirect there.
The posting says Vertex AI; the docs say Agent Platform. Vertex AI Workbench is now "Agent Platform
Workbench", Vertex AI Search is "Agent Search", and Cloud Functions is now "Cloud Run functions". Use both
names in an interview. The table in [role 5](../05-java-fullstack-ai-gemini/details.md) lists the rest.

---

## 1. LangGraph: stateful graphs, memory and multi-agent

**Why:** "Hands-on mastery of multi-agent orchestration patterns, tool calling, stateful graphs, and
memory management (e.g., LangGraph, ...)". LangGraph is the first framework named and the one most
likely to be whiteboarded. [Role 1 section 2](../01-agentic-audit-ai-engineer/details.md#2-stateful-orchestration-with-human-review)
covers interrupts for review at an introductory level; this is the depth.

**You already have:** Step Functions: explicit states, transitions, retries, and state carried between
steps. A LangGraph graph is the same idea with a model inside some nodes.

**Learn:**
- The Graph API: a typed state (TypedDict or Pydantic), nodes as functions over state, normal and
  conditional edges, `START` and `END`. Reducers decide how a node's output merges into state (overwrite
  vs append, as with the messages list). LangGraph is at 1.x (1.2.21 on PyPI, 2026-11-12).
- `Command` for "update state and go to this node" from inside a node, and `Send` for fan-out
  (map-reduce over a list of criteria).
- Persistence: a checkpointer (in-memory for tests, Postgres in production) saves state after every step
  per `thread_id`. That gives you resume after a crash, human-in-the-loop, and time travel (replay or fork
  from an earlier checkpoint).
- Interrupts: `interrupt()` pauses a node and returns a payload to the caller; the run resumes with
  `Command(resume=...)`. A PA case can wait days for a reviewer this way.
- Memory: short-term memory is the thread's state; long-term memory is a store shared across threads
  (namespaced, optionally with semantic search). Know what you would keep per case vs per member vs per
  reviewer, and the PHI consequence of each.
- Multi-agent: subagents (a supervisor calling agents as tools), handoffs, and subgraphs with their own
  state. Know when one agent with more tools beats several agents (usually more often than people think).
- Tool calling inside the graph: a tool node, tool errors returned to the model, and parallel tool calls.
- Testing graphs: run single nodes, use an in-memory checkpointer, and fix model output in tests.
- Observability: tracing every node and tool call; LangSmith is the vendor's option, OpenTelemetry is the
  portable one.

**Links:**
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-graph-api)
- [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
- [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [Time travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel)
- [Memory concepts](https://docs.langchain.com/oss/python/concepts/memory)
- [Add memory](https://docs.langchain.com/oss/python/langgraph/add-memory)
- [Subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)
- [Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)
- [Tools](https://docs.langchain.com/oss/python/langchain/tools)
- [Streaming](https://docs.langchain.com/oss/python/langgraph/streaming)
- [Testing](https://docs.langchain.com/oss/python/langgraph/test)
- [Observability](https://docs.langchain.com/oss/python/langgraph/observability)
- [Application structure](https://docs.langchain.com/oss/python/langgraph/application-structure)
- [langgraph-checkpoint-postgres](https://pypi.org/project/langgraph-checkpoint-postgres/)

**Exercise:** Build the PA intake graph: validate request, fetch member coverage (tool), check
completeness, and either ask for missing information or hand off. Use a Postgres checkpointer. Add an
`interrupt()` before any outcome other than "approve recommended". Kill the process while a case waits,
restart, and resume it with a reviewer decision. Then fork the same case from an earlier checkpoint with
a different reviewer decision and show both histories.

---

## 2. The other named frameworks: AutoGen, Semantic Kernel, LlamaIndex

**Why:** The posting lists "LangGraph, AutoGen, LlamaIndex, Semantic Kernel". You need positioning, not
mastery, for the three you will not build with, and you need to know that two of them have changed.

**Learn:**
- **AutoGen:** the GitHub repo now states it is archived and no longer actively maintained by Microsoft,
  and names Microsoft Agent Framework as its successor. Known for conversational multi-agent patterns
  (agents talking in a group chat). Do not start new work on it; know the migration story.
- **Semantic Kernel:** the repo now says "Semantic Kernel is now Microsoft Agent Framework" and calls the
  new framework its successor. It was Microsoft's SDK for plugins (tools), planners and memory in C#,
  Python and Java, popular in enterprise .NET shops.
- **Microsoft Agent Framework:** the merged successor, at version 1.0 and later (`agent-framework` 1.26.0
  on PyPI, 2026-11-12), Python and .NET. Agents plus graph-based workflows with checkpointing and
  human-in-the-loop, so the concepts map closely onto LangGraph.
- **LlamaIndex:** strongest on the data side: ingestion, parsing (LlamaParse), indexing and retrieval over
  large document sets. Agents and event-driven Workflows exist too (Workflows now sit under its
  "LlamaAgents" docs). A common split is LlamaIndex for retrieval and LangGraph for orchestration.
- One honest sentence for the interview: "I build with LangGraph; I know AutoGen and Semantic Kernel
  were folded into Microsoft Agent Framework, and I would use LlamaIndex where ingestion and retrieval
  are the hard part."

**Links:**
- [AutoGen repository (archived notice)](https://github.com/microsoft/autogen)
- [Semantic Kernel repository (successor notice)](https://github.com/microsoft/semantic-kernel)
- [Microsoft Agent Framework overview](https://learn.microsoft.com/en-us/agent-framework/overview/)
- [Microsoft Agent Framework workflows](https://learn.microsoft.com/en-us/agent-framework/workflows/)
- [Migration guide from AutoGen](https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/)
- [Migration guide from Semantic Kernel](https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-semantic-kernel/)
- [Microsoft Agent Framework repository](https://github.com/microsoft/agent-framework)
- [LlamaIndex framework docs](https://developers.llamaindex.ai/python/framework/)
- [LlamaIndex Workflows](https://developers.llamaindex.ai/python/llamaagents/workflows/)
- [LlamaParse](https://developers.llamaindex.ai/llamaparse/parse/)

**Exercise:** Write a one-page comparison table (state model, persistence, human-in-the-loop, multi-agent
style, maturity, who uses it) for LangGraph, Microsoft Agent Framework and LlamaIndex. Then port one
node of your PA graph, the policy retrieval step, to a LlamaIndex query engine and call it from
LangGraph as a tool.

---

## 3. Vertex AI for ML engineering: Model Garden, endpoints, Vector Search, Workbench

**Why:** "Deep experience with Vertex AI (Model Garden, Endpoint Deployment, Vector Search, Workbench)".
[Role 5 section 4](../05-java-fullstack-ai-gemini/details.md#4-gemini-on-vertex-ai-in-production) covers
calling Gemini; this posting also wants you to deploy and serve models yourself.

**You already have:** quotas, capacity planning, autoscaling and cost control on AWS, plus
private networking. Endpoint deployment is a managed serving fleet, which you know how to run.

**Learn:**
- **Model Garden:** the catalog of Google, partner and open models (Gemma, Llama and others). Model as a
  service (call an API) vs self-deployed (you run the model on your own endpoint and pay for the
  machines). Licenses and model cards matter in healthcare.
- **Self-deployed open models:** one-click deploy from Model Garden, the vLLM serving container, picking
  machine and GPU types, and quota for accelerators. Tuned LoRA adapters can be served the same way.
- **Endpoints:** deploying a model to an endpoint, traffic split between model versions (canary), min and
  max replicas, autoscaling. Endpoint types: shared public, dedicated public, and private (Private Service
  Connect or VPC peering). For PHI, know why you would choose private.
- **Model Registry and custom training jobs:** where tuned models live and how a training job runs, at
  overview level.
- **Vector Search:** built on ScaNN. Indexes and index endpoints, batch vs streaming updates, filtering
  with namespaces (restricts) and numeric filters, dense, sparse and hybrid search, public vs VPC
  endpoints. Know the recall vs latency knobs and that an index on an endpoint costs money while idle.
- **Workbench:** "Agent Platform Workbench" instances are managed JupyterLab VMs. Know idle shutdown,
  service account vs end-user credentials, no public IP, and CMEK for a notebook that may touch PHI.
- **Security controls that apply to all of it:** VPC Service Controls perimeters and CMEK on Agent
  Platform resources (role 6 section 1 covers VPC-SC basics).

**Links:**
- [Model Garden: explore models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-garden/explore-models)
- [Overview of self-deployed models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-garden/self-deployed-models)
- [Deploy and inference tutorial (Model Garden)](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-garden/deploy-and-inference-tutorial)
- [vLLM serving on Cloud GPUs](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/open-models/vllm/use-vllm)
- [Use Gemma open models](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/open-models/use-gemma)
- [Deploy a model to an endpoint](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/general/deployment)
- [Choose an endpoint type](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/predictions/choose-endpoint-type)
- [Model Registry introduction](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/model-registry/introduction)
- [Custom training overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/training/overview)
- [Vector Search overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/vector-search/overview)
- [Vector Search quickstart](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/vector-search/quickstart)
- [Configure index parameters](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/vector-search/configuring-indexes)
- [Create and manage an index](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/vector-search/create-manage-index)
- [Update and rebuild an index](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/vector-search/update-rebuild-index)
- [Filter vector matches](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/vector-search/filtering)
- [Deploy an index to a VPC endpoint](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/vector-search/deploy-index-vpc)
- [Introduction to Agent Platform Workbench](https://docs.cloud.google.com/gemini-enterprise-agent-platform/notebooks/workbench/introduction)
- [VPC Service Controls for Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/general/vpc-service-controls)
- [CMEK for Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/general/cmek)
- [Terraform: google_vertex_ai_index](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/vertex_ai_index)

**Exercise:** In Terraform, create a Vector Search index and a VPC index endpoint, and a Workbench
instance with no public IP. From Model Garden, deploy a small open model to a dedicated endpoint with
min replicas 1. Call both from your PA graph. Record cold-start time, p50/p95 latency and cost per hour,
then undeploy and confirm the bill stops.

---

## 4. Event-driven pipelines: Cloud Run, Pub/Sub, Cloud Run functions

**Why:** "cloud-native services (Cloud Run, Pub/Sub, Cloud Functions)". Role 5 covers a single FastAPI
service on Cloud Run; this is the pipeline between stages. [Role 7 section 6](../07-ai-backend-data-platform/details.md#6-events-and-messaging-kafka-outbox-rabbitmq-redis)
covers messaging correctness (outbox, idempotency) in general.

**You already have:** Lambda, Step Functions, Kinesis and Firehose in production. SQS/SNS-style delivery,
retries and dead-letter handling are concepts you already operate.

**Learn:**
- Cloud Run services vs Cloud Run jobs vs Cloud Run functions (the former Cloud Functions). Pick functions
  for small event handlers, services for anything with real dependencies, jobs for batch re-indexing.
- Pub/Sub: topics, push vs pull subscriptions, at-least-once delivery by default, exactly-once delivery
  (pull subscriptions only), ordering keys, dead-letter topics, retry policy, message filters, schemas.
- Push to Cloud Run with an OIDC token and a dedicated invoker service account, so the subscriber is not
  public.
- Eventarc for routing events (Cloud Storage uploads, audit log events, Healthcare API) to Cloud Run.
- Idempotency: every handler must survive redelivery. Use a case ID plus stage as the idempotency key.
- Long LLM calls: request timeouts, concurrency per instance, and when to move work to a job or to
  Workflows instead of holding an HTTP request open.
- The Healthcare API publishes FHIR store changes to Pub/Sub, which is how a new PA request can start the
  pipeline.

**Links:**
- [What is Cloud Run](https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run)
- [Cloud Run container runtime contract](https://docs.cloud.google.com/run/docs/container-contract)
- [Cloud Run functions overview](https://docs.cloud.google.com/functions/docs/concepts/overview)
- [Compare Cloud Run functions](https://docs.cloud.google.com/run/docs/functions/comparison)
- [Write Cloud Run functions](https://docs.cloud.google.com/run/docs/write-functions)
- [Cloud Run jobs](https://docs.cloud.google.com/run/docs/create-jobs)
- [Pub/Sub overview](https://docs.cloud.google.com/pubsub/docs/overview)
- [Push subscriptions](https://docs.cloud.google.com/pubsub/docs/push)
- [Using Pub/Sub with Cloud Run (tutorial)](https://docs.cloud.google.com/run/docs/tutorials/pubsub)
- [Dead-letter topics](https://docs.cloud.google.com/pubsub/docs/dead-letter-topics)
- [Exactly-once delivery](https://docs.cloud.google.com/pubsub/docs/exactly-once-delivery)
- [Ordering messages](https://docs.cloud.google.com/pubsub/docs/ordering)
- [Subscription message filters](https://docs.cloud.google.com/pubsub/docs/subscription-message-filter)
- [Pub/Sub schemas](https://docs.cloud.google.com/pubsub/docs/schemas)
- [Eventarc overview](https://docs.cloud.google.com/eventarc/docs/overview)
- [Trigger Cloud Run with events](https://docs.cloud.google.com/run/docs/triggering/trigger-with-events)
- [Workflows overview](https://docs.cloud.google.com/workflows/docs/overview)
- [Healthcare API: Pub/Sub notifications](https://docs.cloud.google.com/healthcare-api/docs/how-tos/pubsub)
- [Cloud Run service identity](https://docs.cloud.google.com/run/docs/securing/service-identity)

**Exercise:** Wire four stages (intake, retrieval, criteria check, draft) with Pub/Sub between them, each
a Cloud Run service with its own service account, push subscriptions with OIDC, a dead-letter topic and
a retry policy. Make the criteria stage fail on a poison message and show it lands in the dead-letter
topic. Redeliver a normal message twice and show the case is processed once.

---

## 5. Advanced Python services: asyncio, FastAPI, Pydantic v2, gRPC

**Why:** "Advanced Python expertise (AsyncIO, FastAPI, Pydantic, gRPC) writing clean, tested, and
containerized microservices." FastAPI basics are in [shared section 3](../../shared/details.md#3-tool-calling-and-structured-outputs)
and Cloud Run deployment in [role 5 section 8](../05-java-fullstack-ai-gemini/details.md#8-python-fastapi-services-on-cloud-run).
This section is the "advanced" part a coding interview will probe.

**You already have:** some Python, TypeScript async/await from CDK work, Docker and CI/CD in depth.

**Learn:**
- asyncio properly: the event loop, `async with` and `async for`, `asyncio.TaskGroup` for structured
  concurrency, `asyncio.timeout`, cancellation and cleanup, semaphores to bound concurrent model calls,
  and what blocks the loop (sync SDKs, CPU work) and how to offload it.
- FastAPI beyond the tutorial: dependencies (clients, current user, audit context), lifespan for shared
  clients, `async def` vs `def` handlers, streaming responses, error handlers, bigger-app structure.
- Pydantic v2: models, field and model validators, discriminated unions (one request type per PA
  category), strict mode, `model_validate` and `model_dump`, `pydantic-settings` for config. Know what
  changed from v1.
- gRPC: protobuf (proto3) contracts, unary vs streaming RPCs, deadlines on every call, status codes,
  the health checking protocol, the `grpc.aio` async API, and gRPC on Cloud Run (HTTP/2 end to end).
  When to pick gRPC (internal, typed, streaming) vs REST (edge, browsers, partners).
- Testing: pytest, async tests, dependency overrides, fake model clients so tests are deterministic,
  contract tests for the proto and OpenAPI.
- Quality gates: ruff, mypy, coverage in CI.
- Containers: slim images, uv in Docker, non-root user, one process, graceful shutdown on SIGTERM.

**Links:**
- [asyncio](https://docs.python.org/3/library/asyncio.html)
- [Coroutines and tasks (TaskGroup, timeouts)](https://docs.python.org/3/library/asyncio-task.html)
- [A conceptual overview of asyncio](https://docs.python.org/3/howto/a-conceptual-overview-of-asyncio.html)
- [Developing with asyncio](https://docs.python.org/3/library/asyncio-dev.html)
- [FastAPI: concurrency and async/await](https://fastapi.tiangolo.com/async/)
- [FastAPI: dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI: lifespan events](https://fastapi.tiangolo.com/advanced/events/)
- [FastAPI: bigger applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [FastAPI: async tests](https://fastapi.tiangolo.com/advanced/async-tests/)
- [FastAPI: testing dependencies with overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [FastAPI in containers](https://fastapi.tiangolo.com/deployment/docker/)
- [Pydantic: models](https://pydantic.dev/docs/validation/latest/concepts/models/)
- [Pydantic: validators](https://pydantic.dev/docs/validation/latest/concepts/validators/)
- [Pydantic: settings management](https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/)
- [Pydantic: migration guide from v1](https://pydantic.dev/docs/validation/latest/get-started/migration/)
- [gRPC core concepts](https://grpc.io/docs/what-is-grpc/core-concepts/)
- [gRPC Python quickstart](https://grpc.io/docs/languages/python/quickstart/)
- [gRPC Python basics](https://grpc.io/docs/languages/python/basics/)
- [gRPC asyncio API](https://grpc.github.io/grpc/python/grpc_asyncio.html)
- [gRPC deadlines](https://grpc.io/docs/guides/deadlines/)
- [gRPC status codes](https://grpc.io/docs/guides/status-codes/)
- [gRPC health checking](https://grpc.io/docs/guides/health-checking/)
- [Protocol Buffers proto3 guide](https://protobuf.dev/programming-guides/proto3/)
- [gRPC on Cloud Run](https://docs.cloud.google.com/run/docs/triggering/grpc)
- [pytest](https://docs.pytest.org/en/stable/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/en/latest/)
- [uv in Docker](https://docs.astral.sh/uv/guides/integration/docker/)
- [Ruff](https://docs.astral.sh/ruff/)
- [mypy](https://mypy.readthedocs.io/en/stable/)

**Exercise:** Build a `CriteriaService` in gRPC (`grpc.aio`) that takes a case ID and a list of criteria
and checks them concurrently against the FHIR store with a `TaskGroup`, a semaphore of 5 and a 2-second
deadline per check. Put a FastAPI edge in front of it with Pydantic discriminated unions for request
types. 30+ tests including a cancelled request and a deadline exceeded. Ruff and mypy clean in CI, image
under 200 MB, non-root.

---

## 6. RAG at scale over large document stores

**Why:** "vector indexing, hybrid search, reranking strategies, and chunking optimization for massive
unstructured document stores". The basics on GCP are in [role 5 section 7](../05-java-fullstack-ai-gemini/details.md#7-rag-on-gcp);
this section is the scale and quality layer. Payer medical policies, clinical guidelines, member
contracts and provider manuals are exactly this kind of store.

**Learn:**
- Parsing and chunking: layout-aware parsing (headings, tables, lists), chunks that keep a policy's
  section path ("Policy X > Criteria > 2.b"), parent-child chunks (retrieve small, return the parent),
  contextual chunk headers. Tables of codes and criteria need special handling.
- Metadata as a first-class filter: line of business, plan, state, effective and end dates, policy
  version. Retrieving a retired policy is a correctness bug, not a quality issue.
- Indexing at scale: batch builds vs streaming updates, re-embedding cost when the embedding model
  changes, index versioning and blue-green swaps of an index (you know the pattern from deployments).
- Embedding task types (document vs query) and dimensions.
- Hybrid search: dense for meaning, sparse or keyword for exact terms (drug names, codes, policy IDs),
  fused by reciprocal rank fusion or weighted scores. Vector Search supports hybrid natively; AlloyDB and
  BigQuery are the alternatives if the data already lives there.
- Reranking: a cross-encoder or the Agent Search ranking API over the top 50 to 100 candidates. Measure
  the gain; it costs latency.
- Retrieval evals before answer evals: a labeled query set, recall@k, MRR or nDCG, per-filter slices,
  and regression gates.

**Links:**
- [Vector Search: about hybrid search](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/vector-search/about-hybrid-search)
- [Embedding task types](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/embeddings/task-types)
- [Agent Search ranking API](https://docs.cloud.google.com/generative-ai-app-builder/docs/ranking)
- [RAG Engine: retrieval and ranking](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/rag-engine/retrieval-and-ranking)
- [Document AI: layout parser and chunking](https://docs.cloud.google.com/document-ai/docs/layout-parse-chunk)
- [AlloyDB: hybrid vector similarity search](https://docs.cloud.google.com/alloydb/docs/ai/run-hybrid-vector-similarity-search)
- [BigQuery vector search](https://docs.cloud.google.com/bigquery/docs/vector-search-intro)
- [Reciprocal rank fusion (Elasticsearch reference)](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion)
- [Cross-encoders (Sentence Transformers)](https://www.sbert.net/examples/cross_encoder/applications/README.html)
- [Contextual retrieval (Anthropic)](https://www.anthropic.com/research/contextual-retrieval)
- [BEIR retrieval benchmark](https://github.com/beir-cellar/beir)
- [Ragas](https://docs.ragas.io/en/stable/)

**Exercise:** Generate or assemble at least 2,000 pages of synthetic medical policies with versions and
effective dates. Label 100 queries with the correct policy section. Compare four setups: fixed-size
chunks with dense only, structure-aware chunks with dense only, structure-aware with hybrid, and
structure-aware with hybrid plus reranking. Report recall@10, MRR, p95 latency and cost per 1,000 queries,
and count how often each setup retrieves a retired policy version.

---

## 7. Payer workflows: prior authorization, claims, appeals, member engagement

**Why:** "Proven familiarity with Payer workflows (Prior Authorization, Claims Processing, Appeals, Member
Engagement)". This is the domain the agents work in, and the strong preference in the posting.

**Learn:**
- The players: member, provider (ordering and rendering), payer (health plan), sometimes a utilization
  management vendor or clearinghouse in between. Lines of business: commercial, Medicare Advantage,
  Medicaid managed care, ACA marketplace plans. Rules differ by line.
- **Prior authorization:** the provider asks the payer to approve a service before it is delivered.
  Steps: does this service need PA (coverage requirements), what documentation is needed, submission,
  clinical review against medical policy criteria, decision (approve, deny, pend for more information),
  notification, and appeal. Nurses and medical directors make clinical determinations.
- **The CMS Interoperability and Prior Authorization Final Rule (CMS-0057-F):** applies to Medicare
  Advantage organizations, state Medicaid and CHIP fee-for-service programs, Medicaid managed care plans,
  CHIP managed care entities, and QHP issuers on the federally facilitated exchanges. From January 1,
  2026: decisions within 72 hours for expedited and 7 calendar days for standard requests (these
  timeframes do not apply to QHP issuers on the FFEs), a specific reason for every denial, and public
  reporting of PA metrics (the first set by March 31, 2026). By January 1, 2027: a Prior Authorization
  API, and the Patient Access, Provider Access and Payer-to-Payer APIs. CMS also announced enforcement
  discretion for covered entities that use a FHIR-based Prior Authorization API instead of X12 278.
  Compliance dates vary by payer type; check the CMS page.
- **Claims lifecycle:** provider submits a claim (X12 837), clearinghouse edits, payer adjudication
  (eligibility, coverage, PA match, coding edits, pricing, member cost share), payment and remittance
  (X12 835), denials and resubmissions. Explanation of Benefits to the member.
- **Appeals and grievances:** a member or provider disputes a decision; internal reconsideration, then
  external or independent review depending on line of business. Strict timelines, and the original
  denial reason and evidence have to be retrievable.
- **Member engagement:** outreach, care gaps, plan navigation, explaining a denial in plain language.
  Quality programs such as Medicare Star Ratings drive much of it.
- Where AI helps and where it must not decide alone: summarizing records, matching documentation to
  criteria, drafting letters and citations, routing. Clinical denial decisions stay with people.

**Links:**
- [CMS Interoperability and Prior Authorization Final Rule (CMS-0057-F)](https://www.cms.gov/initiatives/burden-reduction/overview/interoperability/policies-regulations/cms-interoperability-prior-authorization-final-rule-cms-0057-f)
- [CMS-0057-F fact sheet](https://www.cms.gov/newsroom/fact-sheets/cms-interoperability-prior-authorization-final-rule-cms-0057-f)
- [CMS-0057-F in the Federal Register](https://www.federalregister.gov/documents/2024/02/08/2024-00895/medicare-and-medicaid-programs-patient-protection-and-affordable-care-act-advancing-interoperability)
- [CMS interoperability overview](https://www.cms.gov/initiatives/burden-reduction/overview/interoperability)
- [AMA: prior authorization](https://www.ama-assn.org/practice-management/prior-authorization)
- [Medicare FFS prior authorization and pre-claim review initiatives](https://www.cms.gov/data-research/monitoring-programs/medicare-fee-service-compliance-programs/prior-authorization-and-pre-claim-review-initiatives)
- [Medicare Coverage Database (NCDs and LCDs, real coverage criteria)](https://www.cms.gov/medicare-coverage-database/search.aspx)
- [Medicare managed care appeals](https://www.cms.gov/medicare/appeals-grievances/managed-care)
- [Part C and D performance data (Star Ratings)](https://www.cms.gov/medicare/health-drug-plans/part-c-d-performance-data)

**Exercise:** Write a two-page payer primer in your own words: the PA flow as a swimlane diagram
(provider, payer intake, clinical review, notification, appeal) with the CMS-0057-F clocks marked, and
the claims lifecycle from 837 to 835. Then read two real Local Coverage Determinations in the Medicare
Coverage Database and turn their criteria into a checklist your criteria agent could evaluate.

---

## 8. Health data standards: FHIR, Da Vinci, X12, ICD-10, CPT

**Why:** "health data standards (FHIR, EDI X12, ICD-10/CPT)". Every input and output of a payer AI system
is shaped by these.

**You already have:** you have operated EDI integrations at the infrastructure level, so envelopes,
partners, acknowledgments and batch files are not new as operations work.

**Learn:**
- **FHIR R4:** resources, references, Bundles, the REST API and search, profiles and extensions, US Core.
  For payers: Patient, Coverage, Claim, ClaimResponse, ExplanationOfBenefit, Condition, Procedure,
  MedicationRequest, ServiceRequest, DocumentReference.
- **Da Vinci implementation guides for prior authorization:**
  - **CRD (Coverage Requirements Discovery):** the EHR asks the payer, through CDS Hooks, whether a
    service needs PA and what documentation is required.
  - **DTR (Documentation Templates and Rules):** the payer's questionnaire, pre-filled from the record.
  - **PAS (Prior Authorization Support):** the request itself, a Bundle around a Claim sent with the
    `Claim/$submit` operation, answered by a ClaimResponse; `Claim/$inquire` checks status. The current
    published version is v2.2.1 (STU 2) on FHIR R4.
  - Also know CARIN Blue Button (patient access to claims) and PDex (payer data exchange) by name.
- **X12 5010 transactions** named under HIPAA (45 CFR Part 162): 837 claim (professional,
  institutional, dental), 835 payment and remittance advice, 278 health care services review (prior
  authorization request and response), 270/271 eligibility, 276/277 claim status. X12 specifications are
  licensed, so study from the public examples and summaries.
- **Code sets:** ICD-10-CM diagnoses (maintained by CDC's NCHS), ICD-10-PCS inpatient procedures
  (maintained by CMS), CPT procedures (owned and licensed by the AMA), HCPCS Level II supplies, drugs and
  services (CMS). ICD-10-CM and HCPCS are free to use; CPT descriptors are not.
- **Synthetic data:** Synthea generates realistic synthetic patients as FHIR bundles, with no PHI.

**Links:**
- [FHIR R4](https://hl7.org/fhir/R4/)
- [FHIR R4 resource list](https://hl7.org/fhir/R4/resourcelist.html)
- [FHIR R4 RESTful API](https://hl7.org/fhir/R4/http.html)
- [FHIR R4 Bundle](https://hl7.org/fhir/R4/bundle.html)
- [FHIR R4 Claim](https://hl7.org/fhir/R4/claim.html)
- [FHIR R4 ClaimResponse](https://hl7.org/fhir/R4/claimresponse.html)
- [FHIR R4 ExplanationOfBenefit](https://hl7.org/fhir/R4/explanationofbenefit.html)
- [FHIR R4 Coverage](https://hl7.org/fhir/R4/coverage.html)
- [US Core implementation guide](https://hl7.org/fhir/us/core/)
- [Da Vinci project](https://www.hl7.org/about/davinci/)
- [Da Vinci PAS (published)](https://hl7.org/fhir/us/davinci-pas/)
- [Da Vinci PAS (continuous build)](https://build.fhir.org/ig/HL7/davinci-pas/)
- [Da Vinci PAS specification](https://hl7.org/fhir/us/davinci-pas/specification.html)
- [Da Vinci PAS use cases](https://hl7.org/fhir/us/davinci-pas/usecases.html)
- [PAS Claim/$submit operation](https://hl7.org/fhir/us/davinci-pas/OperationDefinition-Claim-submit.html)
- [PAS Claim/$inquire operation](https://hl7.org/fhir/us/davinci-pas/OperationDefinition-Claim-inquiry.html)
- [Da Vinci CRD](https://hl7.org/fhir/us/davinci-crd/)
- [Da Vinci CRD hooks](https://hl7.org/fhir/us/davinci-crd/hooks.html)
- [Da Vinci DTR](https://hl7.org/fhir/us/davinci-dtr/)
- [CDS Hooks](https://cds-hooks.org/)
- [CARIN Blue Button](https://hl7.org/fhir/us/carin-bb/)
- [Da Vinci PDex](https://hl7.org/fhir/us/davinci-pdex/)
- [X12](https://x12.org/)
- [X12 transaction sets](https://x12.org/products/transaction-sets)
- [X12 examples](https://x12.org/examples)
- [45 CFR Part 162 (HIPAA transactions and code sets)](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-162)
- [CMS administrative simplification](https://www.cms.gov/priorities/key-initiatives/burden-reduction/administrative-simplification)
- [CMS: ICD-10 code files (ICD-10-CM and ICD-10-PCS)](https://www.cms.gov/medicare/coding-billing/icd-10-codes)
- [CMS: HCPCS Level II](https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system)
- [AMA: CPT](https://www.ama-assn.org/practice-management/cpt)
- [AMA: CPT code set overview](https://www.ama-assn.org/practice-management/cpt/cpt-code-set-overview)
- [Synthea](https://synthetichealth.github.io/synthea/)
- [Synthea on GitHub](https://github.com/synthetichealth/synthea)

**Exercise:** Generate 500 Synthea patients and load them into a Healthcare API FHIR store (section 9).
For one patient, hand-build a PAS-shaped request Bundle (Claim, Patient, Coverage, Condition with
ICD-10-CM codes, ServiceRequest) and validate it with Pydantic models you write. Then write a half-page
mapping from that Bundle to the main loops of an X12 278 request, based on the public X12 examples, and
note what does not map cleanly.

---

## 9. HIPAA and PHI in AI pipelines on GCP

**Why:** "Deep understanding of HIPAA compliance, PHI handling, and data privacy in AI pipelines."

**You already have:** years of work under NIST 800-53/FISMA and SOX: least privilege, audit trails,
approval gates, change control, evidence for auditors, backup before mutation. The HIPAA Security Rule's
safeguards map closely onto controls you already run. The vocabulary and the PHI-specific rules are new.

**Learn:**
- The rules: Privacy Rule (45 CFR 164 Subpart E), Security Rule (Subpart C: administrative, physical and
  technical safeguards), Breach Notification Rule (Subpart D). Covered entities (payers are one) and
  business associates.
- Minimum necessary (164.502(b)): an agent should get only the fields its step needs. That is a context
  engineering rule and an access control rule at the same time.
- De-identification (164.514): Safe Harbor (remove 18 identifier types) vs Expert Determination. Data
  that is de-identified is no longer PHI; data with a pseudonym usually still is.
- BAA (164.504(e)): Google Cloud offers a BAA, and only the services listed as covered may hold PHI.
  The Google list includes Gemini Enterprise Agent Platform (generative AI on Agent Platform), Workbench
  instances, Cloud Run, Pub/Sub, Cloud Healthcare API and Sensitive Data Protection. Check the current
  list before you design, and check every third-party tool too (tracing vendors, eval tools, model APIs).
  Compliance is shared: the BAA covers Google's side, your configuration is yours.
- Where PHI hides in an AI pipeline: prompts, retrieved chunks, model outputs, embeddings, vector index
  metadata, LangGraph checkpoints and memory stores, traces, logs, eval datasets, notebook outputs,
  cached responses. Each one needs a decision: keep in the secure boundary, de-identify, or never store.
- GCP controls: Cloud Healthcare API (FHIR stores, IAM per dataset and store, de-identify operation),
  Sensitive Data Protection (the former Cloud DLP: inspect, infoTypes, de-identify, pseudonymize with
  format-preserving or deterministic encryption), Cloud Audit Logs (Admin Activity is always on; Data
  Access logs are off by default for most services and must be enabled), CMEK, VPC Service Controls,
  regional resources, Model Armor for prompt and response screening, and the data governance and
  zero data retention terms for generative models.
- Assured Workloads, if the customer needs a compliance regime enforced on the folder.

**Links:**
- [45 CFR Part 164 (Security and Privacy Rules)](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164)
- [45 CFR 164 Subpart C (Security Rule)](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C)
- [45 CFR 164.312 (technical safeguards, audit controls)](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.312)
- [45 CFR 164.502 (uses and disclosures, minimum necessary)](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-E/section-164.502)
- [45 CFR 164.504 (business associate contracts)](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-E/section-164.504)
- [45 CFR 164.514 (de-identification)](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-E/section-164.514)
- [Google Cloud HIPAA compliance](https://docs.cloud.google.com/docs/security/compliance/hipaa)
- [Google Cloud HIPAA overview](https://cloud.google.com/security/compliance/hipaa-compliance)
- [Google Cloud BAA](https://cloud.google.com/terms/hipaa-baa)
- [Cloud Healthcare API introduction](https://docs.cloud.google.com/healthcare-api/docs/introduction)
- [Healthcare API: FHIR concepts](https://docs.cloud.google.com/healthcare-api/docs/concepts/fhir)
- [Healthcare API: create and manage FHIR stores](https://docs.cloud.google.com/healthcare-api/docs/how-tos/fhir)
- [Healthcare API: FHIR resources](https://docs.cloud.google.com/healthcare-api/docs/how-tos/fhir-resources)
- [Healthcare API: import and export FHIR](https://docs.cloud.google.com/healthcare-api/docs/how-tos/fhir-import-export)
- [Healthcare API: de-identification concepts](https://docs.cloud.google.com/healthcare-api/docs/concepts/de-identification)
- [Healthcare API: de-identify FHIR data](https://docs.cloud.google.com/healthcare-api/docs/how-tos/fhir-deidentify)
- [Healthcare API: access control](https://docs.cloud.google.com/healthcare-api/docs/access-control)
- [Healthcare API: audit logging](https://docs.cloud.google.com/healthcare-api/docs/how-tos/audit-logging)
- [Healthcare API: consent management](https://docs.cloud.google.com/healthcare-api/docs/how-tos/consent-managing)
- [Sensitive Data Protection overview](https://docs.cloud.google.com/sensitive-data-protection/docs/sensitive-data-protection-overview)
- [Inspect text for sensitive data](https://docs.cloud.google.com/sensitive-data-protection/docs/inspecting-text)
- [De-identify sensitive data](https://docs.cloud.google.com/sensitive-data-protection/docs/deidentify-sensitive-data)
- [Pseudonymization](https://docs.cloud.google.com/sensitive-data-protection/docs/pseudonymization)
- [infoTypes reference](https://docs.cloud.google.com/sensitive-data-protection/docs/infotypes-reference)
- [De-identification and inspection templates](https://docs.cloud.google.com/sensitive-data-protection/docs/concepts-templates)
- [Cloud Audit Logs](https://docs.cloud.google.com/logging/docs/audit)
- [Enable Data Access audit logs](https://docs.cloud.google.com/logging/docs/audit/configure-data-access)
- [Generative AI zero data retention](https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/zero-data-retention)
- [Model Armor overview](https://docs.cloud.google.com/model-armor/overview)
- [Assured Workloads overview](https://docs.cloud.google.com/assured-workloads/docs/overview)
- [Terraform: google_healthcare_fhir_store](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/healthcare_fhir_store)

**Exercise:** Draw the PHI data-flow map for the portfolio: every store, queue, log, trace, checkpoint,
index and eval file, marked PHI, de-identified or none. Implement three controls and prove each: (1)
traces and logs pass through Sensitive Data Protection de-identification before export, with a test
that a planted member name never reaches them; (2) the eval dataset is produced by the Healthcare API
de-identify operation, not by hand; (3) Data Access audit logs are on for the FHIR store and you can
answer "which service account read this patient's record, and when" with one Logging query.

---

## 10. Fine-tuning small models with PEFT and LoRA

**Why:** "Experience fine-tuning domain-specific models (PEFT, LoRA) for structured extraction or
classification." Supervised tuning of Gemini as a managed service is in [role 5 section 9](../05-java-fullstack-ai-gemini/details.md#9-fine-tuning-on-vertex-ai-supervised-tuning-of-gemini);
this section is tuning an open small model yourself.

**Learn:**
- When to tune: narrow, high-volume, structured tasks (code extraction, document classification, field
  extraction) where a small model can match a large one at a fraction of cost and latency, and where you
  may want the model inside your own boundary. Try prompting and few-shot first and keep them as the
  baseline.
- LoRA: train small low-rank adapter matrices instead of all weights. Rank, alpha, dropout, target
  modules. QLoRA: LoRA on a 4-bit quantized base model to fit on one GPU.
- The Hugging Face stack: `transformers`, `peft` (0.21.x), `trl` SFTTrainer; token classification for
  span extraction vs generative extraction to JSON.
- Running it on GCP: Model Garden LoRA/QLoRA recipes, open-model tuning, or a custom training job;
  serving the adapter on an endpoint (section 3).
- Data: a few hundred to a few thousand clean labeled examples, a held-out test set, no PHI in training
  data unless the whole pipeline is inside the BAA boundary. Use synthetic or de-identified notes.
- Evaluation: exact match and F1 per code, invalid-code rate, latency and cost per 1,000 documents,
  compared with prompting a large model on the same set.

**Links:**
- [PEFT documentation](https://huggingface.co/docs/peft/index)
- [PEFT quicktour](https://huggingface.co/docs/peft/quicktour)
- [LoRA conceptual guide](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora)
- [PEFT quantization (QLoRA)](https://huggingface.co/docs/peft/developer_guides/quantization)
- [TRL SFTTrainer](https://huggingface.co/docs/trl/sft_trainer)
- [Token classification](https://huggingface.co/docs/transformers/tasks/token_classification)
- [LoRA paper](https://arxiv.org/abs/2106.09685)
- [QLoRA paper](https://arxiv.org/abs/2305.14314)
- [Model Garden: LoRA and QLoRA recommendations](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-garden/lora-qlora)
- [Open model tuning](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/open-model-tuning)
- [Create a custom training job](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/training/create-custom-job)

**Exercise:** Generate 2,000 synthetic clinical notes with known ICD-10-CM codes (from Synthea conditions
plus templated text). Fine-tune a small open model with LoRA (or QLoRA) to return the codes as JSON,
validated by Pydantic. Hold out 300 notes. Compare with a large model using a prompt and 5 examples on
F1, invalid-code rate, p95 latency and cost per 1,000 notes. Write down which one you would ship and why.

---

## 11. Evals in CI for probabilistic software

**Why:** "Deep experience with automated LLM benching and continuous integration testing for
probabilistic software." The method (error analysis first, deterministic checks before judges, golden
sets, CI gates) is in [shared section 5](../../shared/details.md#5-verification-and-evals); GCP's Gen AI
evaluation service is in [role 5 section 10](../05-java-fullstack-ai-gemini/details.md#10-evaluation-on-gcp-gen-ai-evaluation-service-and-agent-evals).

**You already have:** CI/CD design and release gating as your day job. The new part is gating on
metrics with variance instead of pass/fail tests.

**Learn (only what is specific to this role):**
- Layered gates for the PA system: schema and FHIR validity (deterministic), retrieval recall@k, citation
  support (does each cited chunk support its criterion), criteria accuracy against labels, and safety
  invariants (no denial without review, no PHI in outputs that leave the boundary). Safety invariants are
  hard gates, not averages.
- Variance: run each case N times, gate on a confidence bound rather than one run, and track flakiness.
- Benchmarks you run yourself: a fixed set, fixed seeds where possible, model and prompt versions pinned,
  cost and latency per run stored next to quality.
- Eval data under HIPAA: de-identified or synthetic only (section 9).
- Agent trajectory checks: did the graph call the right tools in an acceptable order (LangGraph test
  utilities, section 1).

**Links:**
- [Gen AI evaluation service overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/evaluation-overview)
- [LangGraph testing](https://docs.langchain.com/oss/python/langgraph/test)
- [Ragas](https://docs.ragas.io/en/stable/)
- Method, promptfoo and tracing: see [shared section 5](../../shared/details.md#5-verification-and-evals)

**Exercise:** Add a CI job to the portfolio that runs all five layers on 100 labeled synthetic cases, 3
runs each, and fails if recall@10, citation support or criteria accuracy drops below the stored
baseline, or if any case shows a denial that skipped review. Publish the per-run cost in the job summary.

---

## 12. GCP cloud architecture: Terraform, VPCs, IAM (nice-to-have)

**Why:** "Experience with Terraform, GCP VPCs, and IAM fundamentals."

**You already have:** Terraform through Spacelift, deep AWS and Azure IAM and networking. This is the
nice-to-have you are closest to.

**Learn:** everything in [role 6 section 1](../06-platform-engineer-gcp-terraform/details.md#1-gcp-fundamentals-mapped-from-aws)
(hierarchy, IAM, service accounts, Workload Identity Federation, Shared VPC, org policies, VPC Service
Controls), [role 6 section 3](../06-platform-engineer-gcp-terraform/details.md#3-terraform-at-scale-on-gcp)
(Terraform on GCP) and [role 6 section 7](../06-platform-engineer-gcp-terraform/details.md#7-devsecops-on-gcp)
(Secret Manager, Artifact Registry, Binary Authorization). Add only these for this role:

- One service account per pipeline stage, with the narrowest Healthcare API and Vector Search roles.
- Private connectivity for model endpoints and Vector Search (PSC or VPC endpoints), and a VPC-SC
  perimeter around the projects that hold PHI.

**Links:** see role 6 sections 1, 3 and 7.

**Exercise:** Reuse the role 6 foundation module to create a `phi` project and a `tooling` project, then
put the Healthcare API, Vector Search and Agent Platform APIs of the `phi` project inside a VPC-SC
perimeter in dry-run mode and read the violation logs from your own pipeline.

---

## 13. Certifications

**Why:** "GCP Professional Machine Learning Engineer or GCP Professional Cloud Architect credential."
With no production GCP history, a certification is fast third-party proof.

**Learn:**
- **Professional Machine Learning Engineer:** the better fit. The current version covers generative AI,
  including building solutions with Model Garden and Vertex AI Agent Builder and evaluating generative AI
  solutions, plus serving and scaling models, pipelines and monitoring. 2 hours, 50 to 60 questions,
  $200. Google recommends 3+ years of industry experience including 1+ year on Google Cloud.
- **Professional Cloud Architect:** broader cloud design, with 2 case studies on the standard exam. 2
  hours, $200. Closer to what you already know, and covered in
  [role 6 section 12](../06-platform-engineer-gcp-terraform/details.md#12-certification-and-how-to-present-the-background).
- Pick the ML Engineer exam for this posting. Check the exam guide on the certification page before
  studying, since content and product names change.

**Links:**
- [Professional Machine Learning Engineer](https://cloud.google.com/learn/certification/machine-learning-engineer)
- [Professional Cloud Architect](https://cloud.google.com/learn/certification/cloud-architect)

**Exercise:** Book the ML Engineer exam in week 1. Map each exam guide section to a part of the
portfolio, and mark the sections the portfolio does not touch (for example classic ML pipelines) as
extra study.
