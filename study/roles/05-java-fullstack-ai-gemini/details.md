# Role 5: Java Full Stack + AI (Gemini on GCP): details

Material for each item in [highlights.md](highlights.md). All links were checked on 2026-11-13.
Topics already covered in the shared core are linked, not repeated: agent patterns
([shared section 2](../../shared/details.md#2-agent-design-patterns-and-context-engineering)), tool calling
and structured outputs ([shared section 3](../../shared/details.md#3-tool-calling-and-structured-outputs)),
MCP basics ([shared section 4](../../shared/details.md#4-mcp-model-context-protocol)), eval method
([shared section 5](../../shared/details.md#5-verification-and-evals)), LLM security
([shared section 6](../../shared/details.md#6-llm-security)) and Gemini API vs Vertex AI
([shared section 8](../../shared/details.md#8-gemini-and-vertex-ai-basics)). Role 1 covers ADK and Agent
Engine for a different use case, see [role 1 section 1](../01-agentic-audit-ai-engineer/details.md#1-googles-agent-stack-gemini-adk-gemini-enterprise-agent-platform).

**Naming note.** Google has renamed most of this stack. The posting uses the older names; the docs use
the new ones. Know both in an interview:

| Posting / older name | Current docs name |
|---|---|
| Generative AI on Vertex AI | Gemini Enterprise Agent Platform (docs under `docs.cloud.google.com/gemini-enterprise-agent-platform`) |
| Vertex AI Search | Agent Search |
| Vertex AI Agent Engine | Agent Runtime |
| Vertex AI RAG Engine | RAG Engine |
| ADK docs at google.github.io/adk-docs | adk.dev |

---

## 1. Modern Java (17 and 21) and Kotlin awareness

**Why:** "10 to 12 years of experience with Software Development in Java Fullstack (Java, Angular)", and
code "in Angular, TypeScript, Java, Kotlin, Python, or SQL".

**Learn:**
- Records, sealed interfaces, pattern matching for `switch` and `instanceof`, text blocks, `var`
- Collections and streams, `Optional`, immutability, `equals`/`hashCode` contracts
- Exceptions: checked vs unchecked, and where to translate them at service boundaries
- Concurrency: virtual threads (Java 21), `CompletableFuture`, structured thinking about blocking I/O (most LLM calls are slow blocking I/O)
- Build: Maven or Gradle, dependency management, the JDK LTS cadence (17, 21, 25)
- Testing: JUnit, AssertJ, Mockito; test naming and test pyramid
- Kotlin: enough to read and review it (null safety, data classes, coroutines at a high level)

**Links:**
- [dev.java Learn](https://dev.java/learn/)
- [Java SE 21 documentation](https://docs.oracle.com/en/java/javase/21/)
- [Records](https://docs.oracle.com/en/java/javase/21/language/records.html)
- [Pattern matching](https://docs.oracle.com/en/java/javase/21/language/pattern-matching.html)
- [Virtual threads](https://docs.oracle.com/en/java/javase/21/core/virtual-threads.html)
- [JUnit user guide](https://docs.junit.org/6.1.3/overview.html)
- [Kotlin getting started](https://kotlinlang.org/docs/getting-started.html)

**Exercise:** Model a quiz domain in Java 21: a sealed interface `Question` with records
`MultipleChoice`, `ShortAnswer` and `TrueFalse`, a grader that uses a `switch` with pattern matching, and
JUnit tests for every branch. Then call a slow fake "LLM" endpoint 200 times with virtual threads and
with a fixed thread pool, and write down the difference.

---

## 2. Spring Boot backend

**Why:** "design, build, and deploy full-stack web solutions that are reliable, scalable, and
high-performant", and "service architecture ... scalable, distributed services".

**Learn:**
- Spring Boot 3: auto-configuration, profiles, configuration properties, Actuator health and metrics
- REST controllers, Bean Validation, problem-details error responses, API versioning
- Spring Data JPA: entities, repositories, transactions, the N+1 problem, when to drop to SQL
- Flyway migrations as the only way the schema changes
- Testcontainers for real Postgres in tests
- Security: OAuth2 resource server with JWT validation
- Streaming LLM output to the browser: server-sent events from Spring MVC
- Calling Gemini from Java: the Google Gen AI Java SDK directly, or Spring AI's Google GenAI chat client. Know both and why you would pick one

**Links:**
- [Spring Boot project](https://spring.io/projects/spring-boot/)
- [Spring Boot reference](https://docs.spring.io/spring-boot/index.html)
- [Guide: building a RESTful web service](https://spring.io/guides/gs/rest-service/)
- [Guide: accessing data with JPA](https://spring.io/guides/gs/accessing-data-jpa/)
- [Spring Data JPA](https://spring.io/projects/spring-data-jpa/)
- [Spring MVC async requests and SSE](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-async.html)
- [Spring Security OAuth2 resource server](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/index.html)
- [Spring AI: Google GenAI chat](https://docs.spring.io/spring-ai/reference/api/chat/google-genai-chat.html)
- [Google Gen AI Java SDK](https://github.com/googleapis/java-genai)
- [Flyway documentation](https://documentation.red-gate.com/flyway)
- [Testcontainers](https://testcontainers.com/)
- [Spring Boot with Kotlin tutorial](https://spring.io/guides/tutorials/spring-boot-kotlin/)

**Exercise:** Build the portfolio's Spring Boot API: courses, lessons, learners, quiz attempts. Flyway
for the schema, Testcontainers for the tests, Actuator for health. Add one `/quiz/generate` endpoint that
calls Gemini, validates the response into a Java record, and streams progress to the client over SSE.

---

## 3. Angular and TypeScript front end

**Why:** "Java Fullstack (Java, Angular)" and "code in Angular, TypeScript".

**You already have:** daily TypeScript from CDK. Types, generics, async/await and npm tooling carry over.

**Learn:**
- Standalone components, templates, control flow blocks (`@if`, `@for`)
- Signals and computed state; where RxJS still fits (HTTP streams, event streams)
- Routing, lazy loading, guards
- HttpClient, interceptors (auth header, error handling), consuming a streamed response
- Typed reactive forms for the quiz screen
- Testing components and services
- Accessibility basics: a learning product has to work with a keyboard and a screen reader

**Links:**
- [Angular overview](https://angular.dev/overview)
- [Angular tutorials](https://angular.dev/tutorials)
- [Signals](https://angular.dev/guide/signals)
- [HTTP client](https://angular.dev/guide/http)
- [Typed forms](https://angular.dev/guide/forms/typed-forms)
- [Testing](https://angular.dev/guide/testing)
- [TypeScript handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

**Exercise:** Build the Angular UI for the portfolio: a course list, a tutor chat that renders tokens as
they stream in, and a quiz form generated from the structured quiz JSON. Write component tests for the
quiz form, including the empty, loading and error states.

---

## 4. Gemini on Vertex AI in production

**Why:** "Demonstrated track record of deploying Google Gemini models in production using Vertex AI",
and "performance optimization to create user-facing solutions that are both scalable and high-performant".
Basics are in [shared section 8](../../shared/details.md#8-gemini-and-vertex-ai-basics); this is the
production layer.

**You already have:** quota, throttling, retry and cost discipline from AWS and Kubernetes work. The
concepts map directly; only the GCP specifics are new.

**Learn:**
- Model choice and lifecycle: Pro vs Flash vs Flash-Lite, model version retirement dates, pinning versions
- Quotas: Standard PayGo (shared capacity, 429s under load) vs Provisioned Throughput (reserved);
  retry with exponential backoff and jitter; regional vs global endpoints
- Safety filters: categories, thresholds, what a blocked response looks like, and how to show it to a learner
- Structured output with a response schema (see [shared section 3](../../shared/details.md#3-tool-calling-and-structured-outputs))
- Streaming: time to first token is the latency a user feels
- Thinking budgets and levels: quality vs latency vs cost
- Context caching for large repeated context (a whole course chapter)
- Cost: tokens in and out per request, logged and dashboarded; cost per learner session
- Prompt and response screening with Model Armor (prompt injection, sensitive data)

**Links:**
- [Google Gen AI SDKs overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/sdks/overview)
- [Model versions and lifecycle](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-versions)
- [Quotas and system limits](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/quotas)
- [Standard PayGo](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/standard-paygo)
- [Provisioned Throughput](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/provisioned-throughput)
- [Safety filters](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/configure-safety-filters)
- [Structured output](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output)
- [Function calling](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tools/function-calling)
- [Thinking](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/thinking)
- [Context caching](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/context-cache/context-cache-overview)
- [Agent Platform pricing](https://cloud.google.com/model-garden/pricing)
- [Model Armor overview](https://docs.cloud.google.com/model-armor/overview)
- [Google Gen AI Python SDK](https://github.com/googleapis/python-genai)

**Exercise:** Load-test the quiz-generation endpoint at rising request rates until you hit 429s. Add
backoff with jitter, then measure p50 and p95 time to first token and total latency, plus cost per
request, for Flash and Flash-Lite with two thinking settings. Write the results as a one-page table.

---

## 5. Google ADK (Python and Java)

**Why:** "deploying Google Gemini models in production using Vertex AI and the Agent Development Kit
(ADK)" and "agent-based system architectures within the Google Cloud ecosystem".

**Learn:**
- ADK exists in Python, Java, TypeScript, Go and Kotlin. Verified: the Java ADK is
  `com.google.adk:google-adk` on Maven Central (v1.14.0 released 2026-11-02); Python ADK is v2.14.1.
  Python is the most complete; the Java README still lists evaluation as "Coming soon"
- LLM agents, instructions, function tools, agent-as-tool
- Workflows: sequential, parallel, loop, and multi-agent setups (see [shared section 2](../../shared/details.md#2-agent-design-patterns-and-context-engineering) for when to use which)
- Sessions, state and memory: what persists between turns of a tutoring conversation
- Callbacks: before/after model and tool calls, for guardrails and logging
- The dev UI and `adk web` for local debugging
- Deployment targets: Cloud Run (this posting) vs Agent Runtime (formerly Agent Engine). Know the trade-off: Cloud Run gives you control and a familiar container model; Agent Runtime gives managed sessions and memory
- Tracing with Cloud Trace

**Links:**
- [ADK documentation](https://adk.dev/)
- [ADK Python quickstart](https://adk.dev/get-started/python/)
- [ADK Java quickstart](https://adk.dev/get-started/java/)
- [ADK Kotlin quickstart](https://adk.dev/get-started/kotlin/)
- [ADK simple agents](https://adk.dev/agents/llm-agents/)
- [ADK function tools](https://adk.dev/tools-custom/function-tools/)
- [ADK workflows and multi-agent](https://adk.dev/workflows/)
- [ADK conversational context (sessions)](https://adk.dev/sessions/)
- [ADK callbacks](https://adk.dev/callbacks/)
- [Deploy ADK to Cloud Run](https://adk.dev/deploy/cloud-run/)
- [Cloud Trace for ADK](https://adk.dev/integrations/cloud-trace/)
- [Agent Runtime](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/runtime)
- [Quickstart: ADK on Agent Runtime](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/runtime/quickstart-adk)
- [adk-python on GitHub](https://github.com/google/adk-python)
- [adk-java on GitHub](https://github.com/google/adk-java)
- [ADK recipes and samples](https://github.com/google/adk-recipes)

**Exercise:** Build the tutor agent in Python ADK with three tools: `search_course`, `get_learner_progress`
and `generate_quiz`. Add a before-model callback that blocks requests outside the course topic. Deploy
to Cloud Run. Then build the same agent in Java ADK, and write half a page on what was easier or missing
in each.

---

## 6. MCP in ADK

**Why:** "Demonstrated experience with Google ADK, MCP, and integrating Gemini AI APIs into production
web applications." MCP basics are in [shared section 4](../../shared/details.md#4-mcp-model-context-protocol).

**You already have:** daily use of several MCP servers from Claude Code, including their auth and failure modes.

**Learn:**
- `McpToolset` in ADK: connecting an agent to an MCP server over stdio or streamable HTTP. It exists in
  both Python and Java (`com.google.adk.tools.mcp.McpToolset`)
- Filtering which tools from a server the agent may use
- The reverse direction: exposing ADK tools as an MCP server
- Auth for a remote MCP server running on Cloud Run

**Links:**
- [ADK Model Context Protocol tools](https://adk.dev/tools-custom/mcp-tools/)
- [MCP introduction](https://modelcontextprotocol.io/docs/getting-started/intro)

**Exercise:** Write a read-only "learner progress" MCP server backed by the Spring Boot API. Connect it
to the tutor agent with `McpToolset` and a tool filter, and prove the agent cannot reach any write path.

---

## 7. RAG on GCP

**Why:** "RAG Architecture: Proven expertise in designing RAG systems" and "large-scale data retrieval
strategies". The shared core only covers RAG lightly ([shared RAG baseline](../../shared/details.md#retrieval-rag-light-coverage)).

**Learn:**
- Three ways to build it on GCP, and when to pick each:
  - **RAG Engine**: managed corpus, ingestion, chunking, embedding and retrieval; plugs into Gemini as a tool
  - **Agent Search** (formerly Vertex AI Search): managed search with ranking and grounding, least code
  - **pgvector on Cloud SQL or AlloyDB**: full control, data next to your relational data, you own tuning
- Chunking: size, overlap, structure-aware (headings, sections) vs fixed size; keep lesson and section IDs as metadata
- Embeddings: model choice, task types (query vs document), dimensions, re-embedding cost when you switch models
- Hybrid search (keyword plus vector) and reranking
- Metadata filtering: per-course and per-learner scoping, which is also an access-control question
- Grounding and citations: every answer points back to a lesson section
- Retrieval eval: recall@k and MRR on a labeled question set, before you judge any generated answer

**Links:**
- [RAG Engine overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/rag-engine/rag-overview)
- [RAG Engine quickstart](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/rag-engine/rag-quickstart)
- [RAG Engine reranking](https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/rag-engine/retrieval-and-ranking)
- [Agent Search: introduction to custom search](https://docs.cloud.google.com/generative-ai-app-builder/docs/about-generic-search)
- [Agent Search: about retrieval and ranking](https://docs.cloud.google.com/generative-ai-app-builder/docs/ranking-overview)
- [Grounding with Agent Search](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/grounding/grounding-with-vertex-ai-search)
- [Check grounding](https://docs.cloud.google.com/generative-ai-app-builder/docs/check-grounding)
- [Text embeddings](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/embeddings/get-text-embeddings)
- [AlloyDB: work with embeddings](https://docs.cloud.google.com/alloydb/docs/ai/work-with-embeddings)
- [Cloud SQL for PostgreSQL: vector embeddings](https://docs.cloud.google.com/sql/docs/postgres/generate-manage-vector-embeddings)
- [pgvector](https://github.com/pgvector/pgvector)
- [Ragas](https://docs.ragas.io/en/stable/)

**Exercise:** Label 40 questions about the course material with the section that answers each. Build
retrieval twice, once with RAG Engine and once with pgvector on Cloud SQL. Try two chunking strategies on
each. Report recall@5 and MRR for all four combinations, plus cost and latency, and pick one with a
written reason.

---

## 8. Python FastAPI services on Cloud Run

**Why:** "Strong proficiency in Python (FastAPI), Google Cloud Run".

**You already have:** containers, autoscaling, health checks, secrets and service identity from EKS and
Lambda. Cloud Run is the GCP version of what you already operate.

**Learn:**
- FastAPI: path operations, Pydantic request and response models, dependencies, async vs sync handlers
- Running in a container: one process, `PORT`, graceful shutdown, startup probes
- Cloud Run: concurrency per instance, CPU allocation (request-based vs always-on), min instances for
  cold starts, request timeouts for long LLM calls, streaming responses
- Service-to-service auth: Spring Boot calling the agent service with an ID token, no public ingress
- Cloud SQL from Cloud Run, Secret Manager for config
- Deploying from source vs from a built image

**Links:**
- [FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/)
- [FastAPI: concurrency and async](https://fastapi.tiangolo.com/async/)
- [FastAPI in containers](https://fastapi.tiangolo.com/deployment/docker/)
- [Cloud Run: deploy a Python service](https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service)
- [Cloud Run: deploy a Java service](https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-java-service)
- [Cloud Run: deploy from source](https://docs.cloud.google.com/run/docs/deploying-source-code)
- [Cloud Run concurrency](https://docs.cloud.google.com/run/docs/about-concurrency)
- [Cloud Run CPU allocation](https://docs.cloud.google.com/run/docs/configuring/services/cpu)
- [Cloud Run request timeout](https://docs.cloud.google.com/run/docs/configuring/request-timeout)
- [Service-to-service authentication](https://docs.cloud.google.com/run/docs/authenticating/service-to-service)
- [Connect Cloud SQL from Cloud Run](https://docs.cloud.google.com/sql/docs/postgres/connect-run)
- [Secret Manager overview](https://docs.cloud.google.com/secret-manager/docs/overview)

**Exercise:** Deploy the agent service and the Spring Boot API as two Cloud Run services. The agent
service has no public ingress and only accepts ID tokens from the API's service account. Change
concurrency from 80 to 8 under the same load test and explain the effect on latency, instance count and cost.

---

## 9. Fine-tuning on Vertex AI (supervised tuning of Gemini)

**Why:** "Drive AI efforts including Gemini integrations, ML model fine-tuning, evaluation, and
performance optimization" and "ML model fine-tuning, evaluation, and performance optimization for
user-facing systems".

**Learn:**
- When to tune and when not to: try prompting, few-shot and RAG first. Tuning helps with format, style
  and narrow tasks; it does not add fresh knowledge as well as retrieval does
- Supervised fine-tuning: supported models (currently Gemini 2.5 Pro, Flash and Flash-Lite, and newer
  Flash and Flash-Lite versions; check the page), dataset format (JSONL of conversations), train and
  validation splits, epochs, adapter size
- Set the thinking budget to 0 or the thinking level to minimal on tuned tasks, per the docs
- Data quality over data volume: a few hundred clean examples often beat thousands of noisy ones
- Cost: training tokens and serving the tuned endpoint
- Comparing a tuned model against a baseline with the same eval set, never by eye

**Links:**
- [Tuning overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning)
- [About supervised fine-tuning for Gemini](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/supervised-tuning)
- [Prepare supervised tuning data](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/supervised-tuning/prepare-data)
- [Google Cloud Professional ML Engineer certification (syllabus as a checklist)](https://cloud.google.com/learn/certification/machine-learning-engineer)

**Exercise:** Write 300 quiz items in your target style (question, options, answer, explanation keyed to
a lesson section). Tune Gemini Flash-Lite on 250, hold out 50. Compare against prompt-only and 5-shot
Flash on the held-out set for format validity, correctness and cost per 1,000 items. Write down which
you would ship and why.

---

## 10. Evaluation on GCP (Gen AI evaluation service and agent evals)

**Why:** "executing AI performance evaluations to help develop intelligent, user-facing learning
solutions". The method is in [shared section 5](../../shared/details.md#5-verification-and-evals); this is the GCP tooling.

**Learn:**
- Gen AI evaluation service: computation metrics vs model-based (judge) metrics, custom rubrics, pairwise comparison
- Agent evaluation: final response quality and tool-call trajectory
- ADK eval (Python): eval sets of conversations, expected tool calls, `adk eval` in CI
- Layering: deterministic checks first (schema valid, answer key matches, citation exists), then retrieval metrics, then judge metrics
- Learning-specific rubrics: did the tutor give away the answer, is the explanation correct for the level, is it grounded in the course

**Links:**
- [Gen AI evaluation service overview](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/evaluation-overview)
- [Tutorial: evaluation with the Python SDK](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/evaluation-quickstart)
- [Evaluate Gen AI agents](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/evaluation-agents)
- [ADK: why evaluate agents](https://adk.dev/evaluate/)

**Exercise:** Build one CI job that runs three layers: schema checks on 50 generated quizzes, recall@5
on the labeled retrieval set, and a Gen AI evaluation service run with a custom "does not reveal the
answer" rubric over 30 tutor conversations. The job fails if any layer drops below a stored baseline.

---

## 11. Relational schema design and data at scale

**Why:** "Experience of relational database architecture and enterprise data schema management" and
"large-scale data retrieval strategies".

**You already have:** operating databases in production (backups, failover, access). Design depth is the gap.

**Learn:**
- Modeling: entities and relationships, normalization to 3NF and when to denormalize on purpose
- Keys and constraints: surrogate vs natural keys, foreign keys, unique and check constraints as data rules
- Indexes: B-tree, composite index order, partial indexes; reading `EXPLAIN ANALYZE`
- Schema change management: migrations only (Flyway), expand-and-contract for zero-downtime changes
- Scale: partitioning large tables (quiz attempts by month), read replicas, connection pooling from Cloud Run
- Vectors in the same database: pgvector index types and the trade-off of mixing OLTP and vector search
- Event and analytics data: what stays in Postgres and what goes to a warehouse

**Links:**
- [PostgreSQL: data definition](https://www.postgresql.org/docs/current/ddl.html)
- [PostgreSQL: indexes](https://www.postgresql.org/docs/current/indexes.html)
- [PostgreSQL: using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)
- [PostgreSQL: table partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [Flyway documentation](https://documentation.red-gate.com/flyway)

**Exercise:** Design the portfolio schema (courses, lessons, sections, learners, enrollments, quiz
items, attempts, answers, embeddings). Load 5 million synthetic attempts, write the three most common
queries, and use `EXPLAIN ANALYZE` to justify every index. Then do one expand-and-contract migration
(rename a column) with the app running.

---

## 12. Domain-driven design and service architecture

**Why:** "Demonstrated experience with service architecture, domain-driven design, and the development
of scalable, distributed services."

**Learn:**
- Ubiquitous language: the words learners, instructors and the code all share
- Bounded contexts: for example Catalog (courses), Learning (attempts, progress), Tutoring (AI sessions)
- Aggregates and invariants: what must be consistent in one transaction
- A modular monolith first, services only where scaling or ownership differ. In the portfolio, the
  agent service is separate because it has a different runtime (Python), scaling profile and failure mode
- Integration between contexts: synchronous API vs events

**Links:**
- [Domain-driven design (Martin Fowler)](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Bounded context (Martin Fowler)](https://martinfowler.com/bliki/BoundedContext.html)
- [Spring Modulith](https://spring.io/projects/spring-modulith/)

**Exercise:** Draw the bounded contexts for the portfolio, then enforce them in the Spring Boot code with
Spring Modulith so a test fails if Tutoring reaches into Learning's internals.

---

## 13. Kanban, sprints and forecasting

**Why:** "Demonstrated experience running Kanban boards and sprints while forecasting effort for complex
engineering projects."

**You already have:** Kanban and sprint-style work in Jira.

**Learn:**
- Flow metrics: throughput, cycle time, WIP, and Little's law connecting them
- Cumulative flow diagrams: reading bottlenecks and growing WIP
- Forecasting from history (throughput samples, Monte Carlo) rather than from point estimates
- Velocity in sprints and its limits; estimating AI work, where eval results decide when "done" is reached
- Spikes with a time box for uncertain AI work (will tuning beat prompting?)

**Links:**
- [Kanban (Atlassian)](https://www.atlassian.com/agile/kanban)
- [Sprints (Atlassian)](https://www.atlassian.com/agile/scrum/sprints)
- [Estimation (Atlassian)](https://www.atlassian.com/agile/project-management/estimation)
- [Jira cumulative flow diagram](https://support.atlassian.com/jira-software-cloud/docs/view-and-understand-the-cumulative-flow-diagram/)
- [Jira velocity chart](https://support.atlassian.com/jira-software-cloud/docs/view-and-understand-the-velocity-chart/)

**Exercise:** Run the portfolio build on a Kanban board. After 4 weeks, forecast the remaining work with
a simple Monte Carlo over your weekly throughput (a 30-line script is enough), and compare the forecast
with what actually happened at the end.

---

## 14. The learning-product domain

**Why:** "AI-powered learning infrastructure", "AI-powered learning flows" and "intelligent, user-facing
learning solutions" for a "learner-centered team".

**Learn:**
- Tutoring vs answering: guiding questions, hints in steps, checking understanding before moving on
- Learning flows: explain, practice, quiz, feedback, review; mastery and spaced review at a high level
- Quiz quality: one correct answer, plausible distractors, explanation tied to the source
- Learner safety and trust: age-appropriate content, no made-up facts, clear "I am not sure" behavior
- LearnLM: Google's learning-focused model work is now built into Gemini (from the 2.5 series) rather
  than a separate model; know what that means for prompting a tutor

**Links:**
- [LearnLM (Google Cloud)](https://cloud.google.com/solutions/learnlm)
- [LearnLM in the Gemini API docs](https://aistudio.google.com/docs/learnlm)

**Exercise:** Write a one-page tutor behavior spec (when to hint, when to reveal, how to cite), turn
every rule into an eval case for section 10, and run it against two system prompts.
