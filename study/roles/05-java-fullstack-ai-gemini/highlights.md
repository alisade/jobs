# Role 5: Java Full Stack + AI (Gemini on GCP): highlights

Posting: [posting.md](posting.md). The full material list with links is in [details.md](details.md).
Do the [shared core](../../shared/highlights.md) first. This track only adds what this role needs on top of it.

## Where you start

| Posting asks for | You already have |
|---|---|
| "Develop, test, and monitor robust, scalable, and reliable web solutions" | 26 years running production systems: CI/CD, observability, P1 response, root cause |
| Google Cloud Run, "scalable, distributed services" | Containers, Kubernetes fleets, Helm, ArgoCD, AWS Lambda and Step Functions. Cloud Run is a managed container runtime, so the operating model is familiar even though GCP itself is new |
| TypeScript | You write TypeScript every day for CDK. That carries over to Angular, but Angular itself is new |
| Python | Some Python. FastAPI services in production are not proven yet |
| "Unix/Linux environments", "networking", "security" | Linux and Windows fleets, AD/LDAP, least-privilege IAM, network controls |
| Google ADK, MCP | You run and configure MCP servers daily in Claude Code. ADK is new |
| "Running Kanban boards and sprints" | You have run Kanban and sprint-style work in Jira |
| Agent design, tool calling, evals, LLM security | Covered by the shared core (sections 2 to 6) |

## Honest fit note

This is the furthest stretch of all the roles in this repo, if you do not have professional Java and
Angular history. Two minimum qualifications are hard filters, not nice-to-haves:

- "10 to 12 years of experience with Software Development in Java Fullstack (Java, Angular)"
- "Demonstrated track record of deploying Google Gemini models in production using Vertex AI and the
  Agent Development Kit (ADK)"

A few months of study will not produce 10 years of Java. A recruiter screen that reads the minimums
literally will likely stop there, and no study plan changes that. What can make an application credible:

1. **Any real Java or Angular work you have done, stated precisely.** If you have shipped or maintained
   Java or Angular code at any point, find it and lead with it. If you have not, do not imply it.
2. **A deployed, public Gemini + ADK system on GCP**, not a notebook: running on Cloud Run, with
   monitoring, cost per request, quotas handled, an eval suite in CI, and a write-up of what broke.
   That turns "track record in production" from zero into "one system I run and can show you".
3. **A Java 21 / Spring Boot + Angular codebase you can defend line by line** in a technical interview:
   tests, schema migrations, error handling, and the reasons behind each design choice.
4. **Framing as the person who makes AI features survive production**: the reliability, cost, security
   and observability half of the role, where your 26 years are an advantage over a typical app developer.

Apply only after items 2 and 3 exist. Before that, roles 1 and 2 are the better use of an application.

## Gaps, most important first

1. **Modern Java and Spring Boot backend depth.** The core of the role and the biggest gap. Java 21,
   Spring Boot 3, JPA, testing, and Kotlin awareness.
2. **Angular front end.** Components, signals, routing, HttpClient, typed forms, testing. Your TypeScript helps.
3. **Gemini on Vertex AI in production.** Quotas, safety settings, streaming, structured output, thinking
   budgets, context caching, cost. Google now calls this area "Gemini Enterprise Agent Platform".
4. **Google ADK.** Agents, tools, sessions, callbacks, eval, deployment. ADK exists for Python and for
   Java (also TypeScript, Go and Kotlin); eval is still Python-first.
5. **RAG design on GCP.** RAG Engine, Agent Search (formerly Vertex AI Search), pgvector on Cloud SQL or
   AlloyDB, chunking, reranking, retrieval evals.
6. **Fine-tuning and evaluation.** Supervised tuning of Gemini and the Gen AI evaluation service, and
   knowing when tuning beats prompting and RAG.
7. **Python FastAPI services on Cloud Run.** Async, Pydantic, service-to-service auth, concurrency.
8. **Relational schema design and data at scale.** Normalization, indexes, migrations, query plans, partitioning.
9. **Domain-driven design and service architecture.** Bounded contexts, aggregates, when not to split services.
10. **Learning-product domain.** Tutoring and quiz flows, mastery, and why "give the answer" is often the wrong output.

Kanban and sprint forecasting is not a gap. Only the vocabulary (throughput, cycle time, Monte Carlo
forecasts) needs refreshing, see details section 12.

## Plan (after the shared core)

Ten weeks at roughly 10 to 15 hours per week. Java and Angular start early and run in parallel, because
they are the slowest to build credibility in.

| Week | Focus | Output |
|---|---|---|
| 1 | Java 21 language: records, sealed types, pattern matching, streams, virtual threads | 3 small katas in a repo with JUnit tests |
| 2 | Spring Boot 3: REST, validation, JPA, Flyway, Testcontainers | Course and quiz CRUD API with Postgres and tests |
| 3 | Angular: components, signals, routing, HttpClient, typed forms | Angular UI over the week-2 API |
| 4 | Gemini on Vertex AI from Java (Google Gen AI SDK or Spring AI) and Python: streaming, structured output, safety, quotas | Quiz-generation endpoint with schema-validated output, streamed to the UI |
| 5 | Python FastAPI + ADK agent on Cloud Run, called from Spring Boot with service-to-service auth | Tutor agent service with 3 tools, deployed |
| 6 | RAG: RAG Engine and pgvector side by side, chunking experiments, reranking | Retrieval over open course material, with a written comparison |
| 7 | Evals: retrieval metrics, Gen AI evaluation service, ADK eval, CI gate | Eval suite that fails the build on regression |
| 8 | Supervised tuning experiment against a prompt-only baseline, then cost and latency tuning | Tuning report: quality, cost and latency per approach |
| 9 | Schema design review, DDD write-up, MCP tool in ADK, observability (Cloud Trace) | Design doc for the whole system |
| 10 | Polish, README, demo video, interview prep (Java and Angular code walk-through) | Public portfolio repo, ready to show |

## Portfolio project: course tutor on GCP

An AI learning assistant over open course material (for example, an open textbook with a permissive license):

- **Angular** front end: course browser, chat tutor with streamed answers, quiz screen.
- **Spring Boot (Java 21)** API: courses, learners, quiz attempts, progress. Postgres schema with Flyway
  migrations. This is the system of record and owns all writes.
- **Python FastAPI + ADK** agent service on Cloud Run: a tutor agent that retrieves from the course, asks
  guiding questions instead of handing over answers, and calls tools through MCP (for example, a
  "learner progress" MCP server backed by the Spring Boot API, read-only).
- **Gemini on Vertex AI** for generation. Quiz generation uses structured output validated by a schema
  on both sides (Pydantic in Python, a Java record in Spring).
- **RAG** with RAG Engine and pgvector both implemented behind one interface, and the comparison written up.
- **Evals in CI**: retrieval quality (recall@k on a labeled question set), answer quality (groundedness,
  quiz-item correctness), and cost and latency per request. The build fails on regression.
- **Optional**: a small supervised tuning run for quiz-item style, compared against prompt-only and few-shot.
- **Ops**: one Terraform setup, Cloud Run services with least-privilege service accounts, Secret
  Manager, Cloud Trace, a cost dashboard. This is the part where you are strongest; make it visible.

Public repo, open content only, no employer specifics.

## One-line pitch

"I build AI learning features that hold up in production: a Spring Boot and Angular app, a Gemini and
ADK agent on Cloud Run, retrieval and answers measured by evals in CI, and the cost, quota and
reliability work that 26 years of running production systems taught me."
