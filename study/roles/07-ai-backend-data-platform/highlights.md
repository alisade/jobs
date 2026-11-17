# Role 7: AI-driven backend Python/TypeScript developer, data platform -- highlights

Backend platform role at an enterprise data and AI company that is moving its internal business apps off a
third-party CRM onto systems it builds. **On-site in Mountain View, CA**, 6-12 months, via Toptal. The posting
is in [posting.md](posting.md) and the full material list with links is in [details.md](details.md).

Do the [shared core](../../shared/highlights.md) first, but compressed: for this role, shared sections 1
(Claude Code as a platform), 3 (tool calling), 4 (MCP) and 6 (LLM security) matter most. Sections 7 and 8
can wait.

## Where you start

| Posting asks for | You already have |
|---|---|
| Docker, Kubernetes, CI/CD, running services reliably in production | 26 years of this: EKS, Helm, ArgoCD, Jenkins, GitHub Actions, Terraform via Spacelift, P1 incident work |
| Containerized services and deployment pipelines | You build and run the pipelines other teams ship through |
| Workflow automation or orchestration systems | Step Functions, Jenkins pipelines, Kinesis/Firehose delivery; you know retries, timeouts and partial failure from the operator side |
| Messaging (Kafka, RabbitMQ, Redis) | Kinesis and Firehose as infrastructure; shards, ordering and backpressure are familiar concepts |
| PostgreSQL | Operated databases and data pipelines as infrastructure (backups, upgrades, capacity), not as the schema designer |
| TypeScript on the backend (Node.js) | TypeScript daily for CDK and Node runtimes, which is a real head start on syntax, tooling and the type system |
| Python for backend services | Some Python, mostly scripts and automation |
| AI coding tools in the daily workflow (nice to have) | Exact match: heavy daily Claude Code use with your own skills, hooks and MCP servers |
| Agentic/LLM-based applications (nice to have) | You run MCP servers daily and know their failure modes; the shared core turns that into builds |
| Permissions, auditability for agents | Least-privilege IAM, approval gates, pre-push policy hooks, back-up-before-mutate discipline |

## Honest fit note

This is a senior backend engineering role first. The posting says "foundational work, not feature work" and
leads with whiteboarding service boundaries, data models and APIs that other teams depend on. Your
infrastructure depth covers one required bullet fully and makes you unusually strong on "running services
reliably in production", but the interviewers will probe application backend depth: designing a schema for
a complex business domain, explaining a query plan, choosing between a REST and an event interface, and
defending a service boundary. Nothing known about your background shows that yet, so you have to prove it
with a built system and a confident whiteboard session. Pitch yourself as a backend engineer with an
operator's instincts, not as a DevOps engineer who also codes.

## Gaps, most important first

1. **System design and whiteboarding for platforms.** Service boundaries, multi-tenancy, trade-off
   reasoning out loud. This is the interview format and the first months of the job.
2. **PostgreSQL as the schema designer.** Data modeling, indexing, `EXPLAIN ANALYZE`, zero-downtime
   migrations, partitioning, row-level security. "Deep database experience" is a required bullet.
3. **Senior backend service development in Python and TypeScript.** Production-grade FastAPI and Node
   services: async, connection pooling, transactions, testing, error contracts.
4. **API design for other teams.** REST and GraphQL, versioning, idempotency keys, pagination, error
   formats. The posting stresses APIs "that other teams depend on".
5. **Go (or Java).** Required. You have neither on record; Go is the shorter path for you.
6. **Events and messaging as an application developer.** Kafka, the outbox pattern, idempotent consumers,
   RabbitMQ and Redis trade-offs.
7. **Workflow engines as a builder.** Temporal and durable execution, and how agents call into workflow
   primitives. Step Functions gives you a head start.
8. **CRM data models and migration off a CRM.** Salesforce objects, data migration, strangler and
   dual-write strategies. Nice to have, but it is the whole project, so it buys credibility fast.

## Plan (8 weeks, after a compressed shared core)

| Week | Focus | Output |
|---|---|---|
| 0 | Shared core sections 1, 3, 4, 6 | Shared week-2 agent and MCP server, done quickly |
| 1 | System design method, DDIA chapters on data models, replication, partitioning; CRM domain basics | Whiteboard write-up 1: "platform layer for a company leaving its CRM", with an ADR per major decision |
| 2 | PostgreSQL: schema, indexes, `EXPLAIN ANALYZE`, RLS | Portfolio schema with RLS, seeded with 1M synthetic activities, three tuned queries with before/after plans |
| 3 | Python backend: FastAPI, async SQLAlchemy 2 on asyncpg, Alembic, tests | Python accounts/contacts service with idempotency keys, cursor pagination, RFC 9457 errors |
| 4 | TypeScript backend: Fastify, Kysely, Zod; API design and versioning; a GraphQL read layer | TS opportunities/pipeline service plus a small GraphQL read API across both services |
| 5 | Events: outbox, Kafka (Redpanda locally), idempotent consumers, Redis cache | Outbox relay written in Go, a consumer that builds an activity timeline |
| 6 | Temporal: workflows, activities, signals/updates for approvals | Lead-assignment workflow with a human approval step, started from the API |
| 7 | Agents on the platform: scoped MCP tools, audit log; zero-downtime migrations; partitioning | MCP server over the platform, an expand/contract migration done live under load |
| 8 | CRM migration and interview prep | Salesforce-shaped CSV import with reconciliation report; 4 timed mock system design sessions |

## Portfolio project: "own your CRM" platform

A public repo, synthetic data only, that rebuilds a thin slice of what the client is building:

- **Data:** PostgreSQL schema for accounts, contacts, leads, opportunities and activities, multi-tenant
  with row-level security, activities partitioned by month, an append-only audit log.
- **Services with clear boundaries:** a Python FastAPI service that owns accounts and contacts, a
  TypeScript Fastify service that owns opportunities and the sales pipeline. Each owns its tables; they
  talk through APIs and events, never through each other's tables.
- **Events:** a transactional outbox in each service, relayed to Kafka (Redpanda locally) by a small Go
  service. Consumers are idempotent.
- **Workflow primitives:** Temporal workflows for lead assignment with manager approval and for
  opportunity stage changes that need sign-off.
- **Agent surface:** an MCP server exposing a few task-level tools (find account, log activity, propose
  lead assignment). Reads are scoped to the caller's tenant by RLS, writes go through a Temporal
  approval, and every call lands in the audit log.
- **Migration:** an importer for a Salesforce-shaped CSV export (keeping the 18-character legacy IDs) with
  a reconciliation report: row counts, per-object checksums and sampled field diffs.
- **Delivery:** Docker Compose for local, a Helm chart, GitHub Actions CI running tests against a real
  Postgres (Testcontainers), migration linting and a small load test.
- **Docs:** one ADR per major decision and a `docs/query-plans.md` with before/after `EXPLAIN ANALYZE`
  output. The ADRs are your whiteboard practice in written form.

If time runs short, cut in this order: GraphQL layer, Go relay (use a Python poller), Helm chart. Do not
cut RLS, the outbox, the Temporal approval, or the reconciliation report; those are the interview stories.

## One-line pitch

"I have run production platforms for 26 years, and I now build them from the schema up: Postgres models
with tenancy enforced in the database, services with clean boundaries and an outbox, workflows with
approval gates, and agent tools that cannot do more than the user could."
