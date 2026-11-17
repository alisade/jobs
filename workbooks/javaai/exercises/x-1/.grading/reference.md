# Reference: javaai/x-1

A model answer is in `.grading/solution/DESIGN.md`. Key decisions a strong answer makes:

1. Contexts: Catalog (published courses, lessons, sections), Authoring (drafts, review, generation
   requests), Learning (enrollments, attempts, mastery), Tutoring (sessions, transcripts), Tenancy and
   Identity, Analytics (downstream, BigQuery). "Lesson" is a content page in Catalog and a mastery unit in
   Learning (LessonRef by id); "attempt" exists once, in Learning.
2. Drafts never share a table with published items: Authoring owns `draft_item`; publishing creates an
   immutable `quiz_item` version in Catalog through one command. The leak becomes structurally impossible.
3. One modular monolith (Spring Modulith modules Catalog, Authoring, Learning, Tenancy) with
   `ApplicationModules.verify()` in CI; separate services only for tutor-agent and quiz-gen (Python,
   GPU-free but latency and cost profile of LLM calls, different failure mode). The test for a new service:
   different runtime, independent scaling, different failure or compliance boundary, or a separate team
   that cannot share releases.
4. Integration: outbox table per module, relay to Pub/Sub (`attempt.recorded`, `item.published`,
   `learner.deleted`), idempotent consumers keyed by event id; the tutor reads through the MCP server with a
   short timeout and degrades to "I can't see your progress right now".
5. `learning.quiz_attempt` range-partitioned by month on `created_at`, PK `(id, created_at)`, local index
   `(tenant_id, learner_id, course_id, created_at)`; BigQuery via Datastream CDC; drop partitions older than
   4 years after export to the academic archive.
6. Tenancy: `tenant_id` on every row, RLS policies keyed by `current_setting('app.tenant_id')`, set per
   transaction by the API; per-tenant export job. Transcripts in `tutoring.transcript` partitioned by day and
   dropped after 180 days; deletion fans out from `learner.deleted`.
7. Migration: carve modules in place, move tables into per-context schemas with expand-and-contract,
   introduce the outbox, then move draft items out of `quiz_item`.
