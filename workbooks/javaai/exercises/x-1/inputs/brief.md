# Brief: Kestrel course tutor - domain and data design review

From: Head of Engineering, Kestrel Learning (fictional)
To: you, as the senior engineer leading the tutor platform

We are about to grow from one pilot university to twelve. Before we hire two more teams, I want a
design document I can review with the architects and the product lead. Today we have:

- **catalog-api** (Spring Boot 3, Java 21, Cloud SQL for PostgreSQL): courses, lessons, sections,
  quiz items, enrollments, quiz attempts, progress. One codebase, one schema, ~60 JPA entities, every
  team commits to it. It is the system of record and owns all writes.
- **tutor-agent** (Python FastAPI + ADK on Cloud Run): tutoring conversations, calls catalog data
  through the learner-progress MCP server (read-only), Gemini on Vertex AI.
- **quiz-gen** (Python on Cloud Run): generates quiz items with Gemini for authors to review.
- **Angular** learner app and author console.
- A RAG index (pgvector in the same Cloud SQL instance) over lesson sections.

Problems I hear about:

1. The catalog schema is a tangle: "lesson" means a page to authors and a unit of mastery to the
   learning team; "attempt" exists in three tables. Changes in one area break another team's queries.
2. Every new feature asks "should this be a new microservice?" and nobody can say no with reasons.
3. Quiz generation writes draft items straight into `quiz_item` with a `status` column; a bug once
   published drafts to learners.
4. `quiz_attempt` has 41M rows and grows ~6M a month; analytics queries run against the primary.
5. Tutoring sessions are stored in the agent's memory only; Course Ops wants transcripts for review,
   with a 180-day retention limit, and learners can ask for deletion.
6. Universities want their learners' data separated (some contracts say "logically isolated").

What I need from you, in DESIGN.md: bounded contexts and a context map with the ubiquitous language,
aggregates and their invariants, which context owns which writes, how contexts integrate (sync APIs
vs events) with the failure behaviour, which pieces stay one deployable (modular monolith with
Spring Modulith) and which are separate services and why, the relational schema for the core
contexts with keys, constraints and indexes, the plan for quiz attempts at scale (partitioning,
analytics), tenancy for universities, and a migration path from today without a big-bang rewrite.
