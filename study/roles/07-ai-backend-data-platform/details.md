# Role 7: AI-driven backend developer, data platform -- details

Material for each item in [highlights.md](highlights.md). Every topic has the same parts: why it matters,
what you already have (only where true), what to learn, links, and an exercise. All links were checked on
2026-11-13. Shared topics (Claude Code, agent patterns, tool calling, MCP, evals, LLM security) are not
repeated here; each section links to the shared section it builds on.

---

## 1. System design for platforms

**Why:** "Early on you'll spend a lot of time at the whiteboard designing architecture, data models, and
service boundaries" and "Comfort with system design and whiteboarding: able to reason through trade-offs
and explain architectural decisions clearly." This is the interview and the first months of the job.

**You already have:** the operator view of distributed systems: failure modes, capacity, blast radius,
what breaks at 3 a.m. Most candidates lack this; use it in every answer.

**Learn:**
- A repeatable interview method: requirements and non-goals, scale estimates, core entities, API, high-level
  design, then deep dives on the two riskiest parts. Say trade-offs out loud.
- Service boundaries: draw them around data ownership and business capability (accounts, pipeline,
  activities, automation), not around tech layers. One service owns each table; others use its API or events.
- Platform thinking: the customers are other engineers and agents. Stable contracts, self-service
  onboarding, quotas, and a clear "paved road" matter more than feature breadth.
- Multi-tenancy models: shared schema with a `tenant_id` column plus RLS, schema per tenant, database per
  tenant. Know the cost, isolation and noisy-neighbor trade-offs of each. Here "tenant" is likely a
  business unit or app, not an external customer; ask about it in the interview.
- Consistency choices: where you need a transaction, where eventual consistency through events is fine,
  and where a saga or workflow coordinates a multi-service change.
- Architecture Decision Records (ADRs): one page per decision with context, options, decision and
  consequences. It is how a whiteboard session turns into something others can review.

**Links:**
- [Designing Data-Intensive Applications, 2nd edition (O'Reilly)](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/)
- [System Design Primer (GitHub)](https://github.com/donnemartin/system-design-primer)
- [System Design Interview, Alex Xu (book)](https://www.amazon.com/System-Design-Interview-insiders-Second/dp/B08CMF2CQF)
- [ByteByteGo system design interview course](https://bytebytego.com/courses/system-design-interview)
- [Hello Interview: system design in a hurry](https://www.hellointerview.com/learn/system-design/in-a-hurry/introduction)
- [Microservice architecture patterns (microservices.io)](https://microservices.io/patterns/microservices.html)
- [Monolith to Microservices, Sam Newman (O'Reilly)](https://www.oreilly.com/library/view/monolith-to-microservices/9781492047834/)
- [Azure multitenant architecture guide](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/overview)
- [AWS SaaS architecture fundamentals](https://docs.aws.amazon.com/whitepapers/latest/saas-architecture-fundamentals/saas-architecture-fundamentals.html)

**Exercise:** Do four timed 45-minute sessions on a whiteboard (or Excalidraw), recorded, then review them:
(1) the platform layer for a company leaving its CRM, (2) an activity timeline across 10,000 accounts with
50M events, (3) a workflow automation service product teams can self-serve, (4) a tool gateway that lets
agents read and write CRM data safely. Write an ADR for the two hardest decisions in each.

---

## 2. PostgreSQL in depth

**Why:** "Deep database experience, especially PostgreSQL: schema design, query optimization, and data
modeling for complex business domains" and "Design data models and database schemas for core business
entities, with scale, integrity, and migration in mind."

**You already have:** Postgres as infrastructure: backups, upgrades, replicas, capacity and connection
limits. The gap is designing the schema and owning the queries.

**Learn:**
- Modeling: normalize first, then denormalize on purpose. Natural vs surrogate keys (UUIDv7 or bigint
  identity), foreign keys, `CHECK` and `UNIQUE` constraints as business rules, enums vs lookup tables,
  `jsonb` for genuinely open-ended custom fields (a CRM needs this) with GIN indexes, soft deletes and why
  they complicate unique constraints.
- Indexing: B-tree column order, composite and covering (`INCLUDE`) indexes, partial indexes, expression
  indexes, GIN for `jsonb`. Indexes that support keyset pagination.
- Reading plans: `EXPLAIN (ANALYZE, BUFFERS)`, seq scan vs index scan vs bitmap, nested loop vs hash join,
  row estimate errors and stale statistics, `pg_stat_statements` to find the queries worth fixing.
- MVCC and isolation: what Read Committed allows, when to use Serializable or `SELECT ... FOR UPDATE`,
  lock queues, deadlocks, vacuum and bloat.
- Zero-downtime migrations: expand and contract (add new, dual-write or backfill, switch reads, drop old),
  `CREATE INDEX CONCURRENTLY` (cannot run inside a transaction), add constraints as `NOT VALID` then
  `VALIDATE CONSTRAINT`, set `lock_timeout` so a migration fails fast instead of blocking traffic, batch
  backfills. Lint migrations in CI.
- Partitioning: declarative range/list/hash, partition pruning, the rule that a primary key on a
  partitioned table must include the partition key, `pg_partman` for time-based activity tables.
- Row-level security for tenancy: `ENABLE` plus `FORCE ROW LEVEL SECURITY` (owners bypass otherwise), an
  app role without `BYPASSRLS`, policies on `current_setting('app.tenant_id')`, and setting it with
  `SET LOCAL` inside each transaction so it does not leak across pooled connections (PgBouncer in
  transaction mode).

**Links:**
- [PostgreSQL: indexes](https://www.postgresql.org/docs/current/indexes.html)
- [PostgreSQL: using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)
- [PostgreSQL: concurrency control (MVCC)](https://www.postgresql.org/docs/current/mvcc.html)
- [PostgreSQL: transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [PostgreSQL: explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html)
- [PostgreSQL: CREATE INDEX (see CONCURRENTLY)](https://www.postgresql.org/docs/current/sql-createindex.html)
- [PostgreSQL: ALTER TABLE (see NOT VALID)](https://www.postgresql.org/docs/current/sql-altertable.html)
- [PostgreSQL: table partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [PostgreSQL: row security policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [PostgreSQL: CREATE POLICY](https://www.postgresql.org/docs/current/sql-createpolicy.html)
- [PostgreSQL: JSON types](https://www.postgresql.org/docs/current/datatype-json.html)
- [PostgreSQL: pg_stat_statements](https://www.postgresql.org/docs/current/pgstatstatements.html)
- [Use The Index, Luke (SQL indexing for developers)](https://use-the-index-luke.com/)
- [pgMustard: EXPLAIN glossary](https://www.pgmustard.com/docs/explain)
- [explain.dalibo.com (plan visualizer)](https://explain.dalibo.com/)
- [Row-level security for tenants (Crunchy Data)](https://www.crunchydata.com/blog/row-level-security-for-tenants-in-postgres)
- [Parallel change / expand-contract (Martin Fowler)](https://martinfowler.com/bliki/ParallelChange.html)
- [squawk (migration linter)](https://github.com/sbdchd/squawk)
- [pgroll (zero-downtime schema migrations)](https://github.com/xataio/pgroll)
- [pg_partman](https://github.com/pgpartman/pg_partman)

**Exercise:** Build the portfolio schema, seed 1M activities across 200 tenants, and pick three slow
queries (account timeline, "my open opportunities", search by custom field). For each, save the plan
before and after your fix with a one-paragraph explanation. Then prove RLS works: connect as the app role,
forget to set the tenant, and show zero rows rather than all rows.

---

## 3. Backend Python: FastAPI, async, SQLAlchemy 2, asyncpg

**Why:** "Strong production experience with Python for backend services" and "Design and build backend
services in Python and TypeScript."

**Learn:**
- FastAPI: path operations, Pydantic models as request/response contracts, dependency injection (for the
  DB session, the current user and tenant), lifespan events, background tasks and their limits.
- Async correctly: what blocks the event loop, `async def` vs `def` endpoints in FastAPI, timeouts and
  cancellation, bounded concurrency.
- SQLAlchemy 2.0 style: `select()` statements, the async engine on the asyncpg driver, one session per
  request, explicit transactions, eager loading to avoid N+1, connection pool sizing against Postgres
  `max_connections`.
- Setting the RLS tenant per transaction (`SET LOCAL` through `set_config(..., true)`) inside the session
  dependency.
- Alembic migrations, autogenerate and why you still review every generated file.
- Testing: pytest with a real Postgres (Testcontainers), dependency overrides, contract tests on the
  OpenAPI schema.
- Choice: FastAPI plus SQLAlchemy 2 is the default in most Python shops and pairs with the Pydantic
  skills from the shared core. Raw asyncpg is worth knowing for hot paths and bulk loads (`COPY`).

**Links:**
- [FastAPI: concurrency and async/await](https://fastapi.tiangolo.com/async/)
- [FastAPI: dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI: testing with dependency overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [SQLAlchemy 2.0 unified tutorial](https://docs.sqlalchemy.org/en/20/tutorial/index.html)
- [SQLAlchemy asyncio extension](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [asyncpg docs](https://magicstack.github.io/asyncpg/current/)
- [Alembic docs](https://alembic.sqlalchemy.org/en/latest/)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [Testcontainers](https://testcontainers.com/)
- Pydantic, FastAPI basics and uv: see [shared section 3](../../shared/details.md#3-tool-calling-and-structured-outputs)

**Exercise:** Build the accounts/contacts service: CRUD plus search, cursor pagination, idempotency keys on
create, RFC 9457 error bodies, tenant set per transaction. Load-test it with 200 concurrent clients, find
the first bottleneck (likely the pool or an N+1), fix it, and write down what you found.

---

## 4. Backend TypeScript: Node.js, Fastify, Kysely

**Why:** "Strong production experience with TypeScript on the backend (Node.js)."

**You already have:** TypeScript every day for CDK and Node runtimes: the type system, npm/bun tooling and
async/await. The gap is long-running HTTP services and their data layer.

**Learn:**
- The Node event loop: what blocks it, worker threads for CPU work, graceful shutdown on SIGTERM (you know
  why this matters in Kubernetes), keep-alive and timeouts.
- Framework pick: **Fastify.** It is small, fast and schema-first (JSON Schema validation and
  serialization per route), which matches API-contract-first design. NestJS is the other common choice:
  heavier, decorator- and DI-based, popular in larger teams. Learn to read a NestJS codebase in case the
  client uses it, but build in Fastify.
- Data layer pick: **Kysely.** A type-safe SQL query builder: you still write SQL-shaped queries, so your
  Postgres work (indexes, plans, `SET LOCAL` for RLS inside a transaction) carries over directly, and
  there is no hidden query generation to fight. Drizzle is a close alternative with a similar SQL-first
  feel. Prisma is the most popular ORM and fine for CRUD, but it abstracts SQL more, and per-transaction
  session settings for RLS take extra work. Know all three well enough to discuss.
- Runtime validation with Zod at the edges (config, inbound events), shared types between services.
- Testing with a real Postgres, structured logging, OpenTelemetry traces.

**Links:**
- [Node.js: the event loop, timers and nextTick](https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick)
- [Fastify docs](https://fastify.dev/docs/latest/)
- [Kysely docs](https://kysely.dev/docs/intro)
- [Drizzle ORM docs](https://orm.drizzle.team/docs/overview)
- [Prisma docs](https://www.prisma.io/docs)
- [NestJS docs](https://docs.nestjs.com/)
- [Zod](https://zod.dev/)

**Exercise:** Build the opportunities/pipeline service in Fastify and Kysely: stage transitions with
validation rules enforced in a transaction (`SELECT ... FOR UPDATE` on the opportunity), an outbox row
written in the same transaction, and graceful shutdown that drains in-flight requests. Kill a pod during a
load test and show zero failed requests.

---

## 5. API design for platforms other teams depend on

**Why:** "Experience designing and building backend services and APIs (REST and/or GraphQL) that other
teams depend on" and "service interfaces (APIs, events, integrations) that product teams and agentic apps
can build on."

**Learn:**
- Resource-oriented REST: nouns, standard methods, field masks or partial updates, consistent errors
  (RFC 9457 problem details), OpenAPI as the contract, generated clients.
- Idempotency keys for every create and every side-effecting call: store key, request hash and response;
  replay the stored response on retry; reject a reused key with a different body. Agents and workflow
  activities retry, so this is not optional on this platform.
- Pagination: cursor/keyset, not offset, for large tables; stable sort keys; opaque cursors.
- Versioning and evolution: additive changes only within a version, deprecation windows, never change the
  meaning of a field. Consumers you do not know about will break.
- GraphQL: when it fits (a read layer that joins accounts, contacts and opportunities for UI and agent
  clients) and when it does not (write-heavy command APIs). Connections-style pagination, N+1 and
  DataLoader, field-level authorization, query cost limits.
- Sync vs async interfaces: when to expose an API, when to publish an event, when to start a workflow.

**Links:**
- [Google API design guide](https://docs.cloud.google.com/apis/design)
- [AIP-158: pagination](https://google.aip.dev/158)
- [RFC 9457: problem details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)
- [IETF draft: the Idempotency-Key HTTP header](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/)
- [Stripe: idempotent requests](https://docs.stripe.com/api/idempotent_requests)
- [Implementing Stripe-like idempotency keys in Postgres (Brandur Leach)](https://brandur.org/idempotency-keys)
- [OpenAPI Initiative](https://openapis.org/)
- [GraphQL: learn](https://graphql.org/learn/)
- [GraphQL: best practices](https://graphql.org/learn/best-practices/)
- [GraphQL: pagination](https://graphql.org/learn/pagination/)
- [GraphQL: authorization](https://graphql.org/learn/authorization/)
- [Relay cursor connections spec](https://relay.dev/graphql/connections.htm)
- [Apollo: schema design](https://www.apollographql.com/docs/graphos/schema-design)

**Exercise:** Write the OpenAPI spec for both portfolio services before writing code (spec-first, see
[shared section 7](../../shared/details.md#7-spec-driven-development)). Then add a GraphQL read endpoint
that returns an account with its contacts and open opportunities, and show with query logs that DataLoader
removed the N+1.

---

## 6. Events and messaging: Kafka, outbox, RabbitMQ, Redis

**Why:** Nice to have: "Experience with messaging and caching systems such as Kafka, RabbitMQ, or Redis."
Required in practice: "service interfaces (APIs, events, integrations)" and "complex, distributed backend
systems".

**You already have:** Kinesis and Firehose as infrastructure. Shards map to Kafka partitions, consumer
checkpoints to consumer-group offsets, and Firehose delivery to a Kafka Connect sink. What is new is
writing producers and consumers that are correct.

**Learn:**
- Kafka model: topics, partitions, keys and per-key ordering (key by account ID), consumer groups,
  offsets, retention, compaction, delivery semantics, idempotent producer.
- The dual-write problem: writing to the database and publishing to Kafka are two systems and one of them
  will fail. Transactional outbox: write the event row in the same transaction as the change, relay it by
  polling or by CDC (Debezium outbox router).
- Consumers are at-least-once, so make them idempotent: a processed-event table or natural idempotency.
  Dead-letter topics, poison messages, replay.
- Event design: thin notification vs full state, schema evolution, versioned event types.
- RabbitMQ vs Kafka: work queues with acks and routing vs a replayable log. Pick by whether consumers need
  history.
- Redis: cache-aside with explicit TTLs and invalidation, rate limiting, streams; know the limits of Redis
  locks (use database constraints or workflow engines for correctness-critical mutual exclusion).
- Sagas for multi-service changes, and when a workflow engine is a better home for one (section 7).

**Links:**
- [Kafka introduction](https://kafka.apache.org/intro/)
- [Kafka documentation (see message delivery semantics)](https://kafka.apache.org/documentation/#semantics)
- [Redpanda quick start (Kafka-compatible, easy locally)](https://docs.redpanda.com/streaming/current/get-started/quick-start/)
- [Transactional outbox pattern (microservices.io)](https://microservices.io/patterns/data/transactional-outbox.html)
- [Saga pattern (microservices.io)](https://microservices.io/patterns/data/saga.html)
- [Debezium outbox event router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html)
- [RabbitMQ tutorials](https://www.rabbitmq.com/tutorials)
- [RabbitMQ reliability guide](https://www.rabbitmq.com/docs/reliability)
- [Redis docs](https://redis.io/docs/latest/)
- [Redis streams](https://redis.io/docs/latest/develop/data-types/streams/)
- [Redis distributed locks (read the caveats)](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)

**Exercise:** Implement the outbox in both services and a relay to Redpanda (in Go, see section 9). Write
a consumer that builds the activity timeline. Then break it on purpose: kill the relay mid-batch, deliver
duplicates, reorder two partitions. Show the timeline ends up correct and explain why.

---

## 7. Workflow automation primitives and durable execution

**Why:** "Build workflow automation primitives and service interfaces ... that product teams and agentic
apps can build on" and "Experience with workflow automation or orchestration systems, or with
agentic/LLM-based applications."

**You already have:** Step Functions and Jenkins pipelines: retries, timeouts, state, partial failure and
human approval steps from the operator side. Temporal is the same idea expressed as code.

**Learn:**
- Durable execution: workflow code whose state survives crashes because every step is recorded in an
  event history and replayed. Workflows must be deterministic; all side effects (DB writes, API calls,
  LLM calls) live in activities with retry policies and timeouts.
- Signals, queries and updates: how a human approval or an external event reaches a running workflow.
  Timers for "escalate if not approved in 48 hours".
- Workflow versioning: changing code while old executions are still running.
- What a "primitive" means here: a small catalog of reusable, well-tested workflows (assign, approve,
  notify, sync, escalate) with typed inputs, exposed through an API so product teams do not touch the
  engine directly.
- How agentic apps consume them: the agent does not hold long-running state or perform risky writes
  directly. It calls a tool that starts a workflow, the workflow enforces approval and retries, and the
  agent can query status later. An LLM call inside a workflow is an activity, never workflow code, because
  it is non-deterministic.
- Temporal vs Step Functions vs a queue plus cron: be ready to compare on developer experience, testing,
  vendor lock-in and long-running human steps.

**Links:**
- [Temporal docs](https://docs.temporal.io/)
- [What is durable execution (Temporal)](https://temporal.io/blog/what-is-durable-execution)
- [Temporal: workflows](https://docs.temporal.io/workflows)
- [Temporal: activities](https://docs.temporal.io/activities)
- [Temporal: event history](https://docs.temporal.io/encyclopedia/event-history)
- [Temporal: signals, queries and updates](https://docs.temporal.io/sending-messages)
- [Temporal Python SDK guide](https://docs.temporal.io/develop/python)
- [Temporal Python: message passing](https://docs.temporal.io/develop/python/workflows/message-passing)
- [Temporal TypeScript SDK guide](https://docs.temporal.io/develop/typescript)
- [Temporal courses](https://learn.temporal.io/courses/)
- [Temporal Python samples](https://github.com/temporalio/samples-python)
- [Temporal TypeScript samples](https://github.com/temporalio/samples-typescript)
- Workflow vs agent: see [shared section 2](../../shared/details.md#2-agent-design-patterns-and-context-engineering)

**Exercise:** Build the lead-assignment workflow: score the lead (activity), propose an owner, wait for a
manager approval update with a 48-hour timer that escalates, then write the assignment through the
accounts API with an idempotency key. Kill the worker in the middle of each step and show it resumes.
Then write the same flow as a Step Functions state machine on paper and list what differs.

---

## 8. CRM data models and migrating off a CRM

**Why:** "moving their first-party business applications off a major third-party CRM platform",
"replace capabilities currently provided by a third-party CRM platform", "Contribute to migration
planning", and nice to have: "Familiarity with CRM data models (e.g., Salesforce) or experience migrating
off a CRM platform."

**Learn:**
- The core Salesforce objects and their relationships: Account, Contact, Lead (converts into Account,
  Contact and Opportunity), Opportunity (with stages and line items), Opportunity Contact Role, User and
  record ownership, and activities (Task and Event, which point at a Lead or Contact through `WhoId` and at
  an Account, Opportunity or other record through the polymorphic `WhatId`).
- Custom objects and fields (`__c`), record types, picklists, 15- vs 18-character IDs. Keep the legacy ID in
  an indexed column on every migrated row so you can reconcile and so integrations can look records up.
- Hidden business logic: validation rules, flows, triggers, formula and roll-up fields, sharing rules.
  These are what the new platform actually has to replace; inventory them before modeling.
- Extraction: Bulk API 2.0 for large exports, Change Data Capture for ongoing changes during the
  transition.
- Migration strategy: strangler fig (move one capability or app at a time behind a routing layer), a
  one-way sync from the old system while it is still the source of truth, then flip the source of truth
  per capability. Prefer CDC-driven sync over application dual-write; dual-write needs reconciliation and
  conflict rules for when the two sides disagree.
- Reconciliation as a first-class deliverable: row counts per object, checksums over normalized fields,
  sampled field-by-field diffs, orphan checks on foreign keys, and a rollback plan per cutover.

**Links:**
- [Trailhead: data modeling (objects, fields, relationships)](https://trailhead.salesforce.com/content/learn/modules/data_modeling)
- [Trailhead: leads and opportunities](https://trailhead.salesforce.com/content/learn/modules/leads_opportunities_lightning_experience)
- [Trailhead: Salesforce API basics (REST, SOAP, Bulk)](https://trailhead.salesforce.com/content/learn/modules/api_basics)
- [Trailhead: Change Data Capture basics](https://trailhead.salesforce.com/content/learn/modules/change-data-capture)
- [Trailhead: optimizing large data volumes](https://trailhead.salesforce.com/content/learn/modules/large-data-volumes)
- [Trailhead: importing and exporting data](https://trailhead.salesforce.com/content/learn/modules/lex_implementation_data_management)
- [Strangler application pattern (microservices.io)](https://microservices.io/patterns/refactoring/strangler-application.html)
- [Strangler fig application (Martin Fowler)](https://martinfowler.com/bliki/StranglerFigApplication.html)

**Exercise:** Generate a Salesforce-shaped CSV export (Accounts, Contacts, Leads, Opportunities, Tasks with
`WhoId`/`WhatId`, a few custom fields, some deliberately broken rows). Write the importer and a
reconciliation report. Then write a one-page cutover plan for moving one internal app: phases, source of
truth per phase, how you detect drift, and how you roll back.

---

## 9. Go basics

**Why:** "Experience with Go or Java" is a required bullet, and Go and Java are both in the listed skills.

**Pick Go, not Java.** Kubernetes, Helm, Terraform, Docker and most of the tooling you already run are
written in Go, so you can read their source when debugging and your Go will show up in exactly the kind of
platform glue this team needs (relays, sidecars, CLIs, operators). Go is small, compiles to one static
binary, and takes weeks rather than months to become productive in. Java is the better pick only if the
client's existing services are on the JVM; ask in the interview. If they are, read the
[dev.java learning path](https://dev.java/learn/) for syntax and the JVM basics.

**Learn:**
- The language: types, structs and interfaces, errors as values, `defer`, goroutines, channels, `select`.
- `context.Context` for cancellation and deadlines through every call.
- `net/http` servers and clients, timeouts, graceful shutdown.
- Postgres from Go with `pgx`; `database/sql` basics.
- Module layout, `go test`, table-driven tests, `go vet`, building small container images.

**Links:**
- [A Tour of Go](https://go.dev/tour/)
- [Effective Go](https://go.dev/doc/effective_go)
- [Go by Example](https://gobyexample.com/)
- [Go tutorial: accessing a relational database](https://go.dev/doc/tutorial/database-access)
- [Go: organizing a module](https://go.dev/doc/modules/layout)
- [Go: context package](https://pkg.go.dev/context)
- [Go: net/http package](https://pkg.go.dev/net/http)
- [pgx (Postgres driver for Go)](https://pkg.go.dev/github.com/jackc/pgx/v5)

**Exercise:** Write the outbox relay in Go: poll the outbox table with `FOR UPDATE SKIP LOCKED` in batches,
publish to Redpanda, mark rows sent, expose `/healthz` and Prometheus metrics, and shut down cleanly on
SIGTERM. Run two replicas and show no event is published twice by the relay itself.

---

## 10. Agentic apps on the platform: tool APIs, permissions, audit

**Why:** "the platform layer that will power agentic apps and workflow automation across the company" and
"service interfaces ... that product teams and agentic apps can build on."

**You already have:** daily use of MCP servers against real systems, and the least-privilege and
approval-gate habits from infrastructure work.

**Learn:**
- Tool APIs designed around tasks ("log a call with this contact", "propose an owner for this lead"), not
  one tool per table or per REST endpoint. See [shared section 4](../../shared/details.md#4-mcp-model-context-protocol)
  and [shared section 3](../../shared/details.md#3-tool-calling-and-structured-outputs).
- Identity: an agent acts on behalf of a user. Pass the user and tenant through to the platform (OAuth
  token exchange or a signed delegation claim) so the database's RLS applies to the agent exactly as it
  would to the user. The agent never gets a broader role than the human.
- Writes: read tools open, write tools idempotent and routed through workflow approvals where the action is
  risky or irreversible (section 7). See [shared section 6](../../shared/details.md#6-llm-security) for
  why tool scoping, not model behavior, is the control.
- Audit log: append-only table with actor, on-behalf-of user, agent or app ID, tool, arguments hash,
  result, trace ID and timestamp. Queryable by the people who will ask "what did the agent change?".
- Guardrails at the platform layer: per-agent rate limits and quotas, payload size limits, and evals on
  tool usage (see [shared section 5](../../shared/details.md#5-verification-and-evals)).

**Links:**
- [MCP specification: authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)
- [OWASP logging cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- [Writing effective tools for agents (Anthropic)](https://www.anthropic.com/research/writing-tools-for-agents)

**Exercise:** Build the portfolio MCP server with four tools: `find_account`, `get_account_timeline`,
`log_activity`, `propose_lead_assignment` (starts the Temporal workflow, does not assign). Connect it to
Claude Code as two different synthetic users in two tenants and show each sees only its own data, the
proposal waits for approval, and every call is in the audit log. Add one injection test from the shared
security exercise.

---

## 11. Delivery and reliability, framed for backend

**Why:** "Build and maintain the supporting infrastructure: containerized services, deployment pipelines,
and the systems that keep everything reliable in production." This is your strongest area; the work is
in showing it from the service owner's side.

**You already have:** all of it at production scale: Docker, EKS, Helm, ArgoCD, CI/CD, observability,
incident response.

**Learn:**
- What a service owner adds: readiness vs liveness that reflect real dependencies, migrations as a separate
  job that runs before the rollout, SLOs per API, traces that cross the outbox and Kafka boundary.
- Testing with real dependencies in CI (Testcontainers), migration linting, contract tests between services.

**Links:**
- [Docker Compose](https://docs.docker.com/compose/)
- [Helm docs](https://helm.sh/docs/)
- [Testcontainers](https://testcontainers.com/)

**Exercise:** Give the portfolio a Helm chart with a pre-upgrade migration job, a GitHub Actions pipeline
that runs tests against real Postgres and Redpanda, squawk on every migration, and a k6 or Locust smoke
load test. In the interview, walk through it as "how I would run this platform", which is where you are
ahead of other candidates.
