# Rubric: javaai/x-1 Bounded contexts, write ownership and the schema for twelve universities
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Design exercise: grade.sh reports 0/0; this row does not apply. |
| 2 | Language and contexts | 15 | Resolves the "lesson" and "attempt" ambiguities with per-context definitions; 4-6 contexts with clear ownership and a context map (relationships named, ACL where the Python services consume catalog data). |
| 3 | Aggregates and invariants | 15 | Real invariants per aggregate (an attempt references a published item of an enrolled course; mastery derived from attempts; draft items live in Authoring and become a separate published item only through review), transaction boundaries, what is eventually consistent. |
| 4 | Integration and write ownership | 15 | Every write has one owner; events via transactional outbox to Pub/Sub with idempotent consumers; sync reads with timeouts and degraded behaviour; the tutor and quiz-gen never write the system of record directly. |
| 5 | Deployment boundaries | 15 | Modular monolith first with Spring Modulith modules and verified dependencies; separate services only for different runtime, scaling or failure mode (tutor, quiz-gen) with reasons; an explicit test for the next "new microservice" request. |
| 6 | Schema and scale | 20 | Concrete tables with PKs, FKs, unique and check constraints; indexes justified by named queries; quiz_attempt range-partitioned by month with tenant and learner leading the local indexes; analytics to BigQuery via CDC or events, read replica for heavy reads; 4-year retention by partition drop. |
| 7 | Tenancy, privacy and migration | 20 | tenant_id on every tenant-owned row with PostgreSQL row-level security (or schema-per-tenant with reasons), per-tenant export; learner deletion and 180-day transcript retention (partitioned or TTL'd store, no transcripts in the agent's memory); a stepwise migration (modules, expand-and-contract, outbox, strangle quiz drafts out of quiz_item) with checks for each step. |
Total: 100
