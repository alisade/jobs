# Design: Kestrel course tutor - bounded contexts, data and service boundaries

## Ubiquitous language

| Term | Context | Meaning |
|---|---|---|
| Course | Catalog | A published course: title, lessons in order, owned by a tenant |
| Course run | Learning | One offering of a course to a cohort with dates; learners enroll in a run |
| Lesson | Catalog | A content page made of sections (what authors write) |
| Lesson (mastery unit) | Learning | A LessonRef (id) the learner masters by passing its quiz |
| Draft item | Authoring | A quiz item being written or generated; never visible to learners |
| Quiz item | Catalog | A published, immutable item version |
| Attempt | Learning | One learner answer to one quiz item version; the only table called attempt |
| Mastery | Learning | Derived: a lesson is mastered when its quiz rule is met by attempts |
| Tutor session | Tutoring | One conversation with the AI tutor, with a transcript |

## Bounded contexts and context map

```text
            +-----------+   published items (event)   +-----------+
            | Authoring |---------------------------->|  Catalog  |
            | drafts,   |<----- read lessons ---------| courses,  |
            | review    |                             | lessons   |
            +-----+-----+                             +-----+-----+
                  | generation requests                     | lessons, items (read)
                  v                                         v
            +-----------+                             +-----------+    attempt.recorded
            |  quiz-gen | (Python, separate service)  | Learning  |--------------------> Analytics
            +-----------+                             | runs,     |                      (BigQuery)
                                                      | attempts, |
            +-----------+   read via MCP (ACL)        | mastery   |
            |  Tutoring |---------------------------->|           |
            | sessions, |                             +-----------+
            | transcripts (tutor-agent, Python)
            +-----------+
            Tenancy and Identity: upstream of all (tenant_id, learner identity, roles)
```

Relationships: Catalog is upstream of Learning (customer/supplier). Tutoring consumes Learning and
Catalog through the read-only MCP server, which is its anti-corruption layer. Analytics is a
conformist consumer of events. Authoring publishes into Catalog through one command.

## Aggregates and invariants

- Catalog: `Course` (root) with `Lesson` and `Section`; invariant: lesson positions unique and contiguous
  within a course version. `QuizItem` is its own aggregate, immutable once published (new version on change).
- Authoring: `DraftItem` (root) with review state DRAFT -> IN_REVIEW -> APPROVED; only APPROVED drafts can be
  published, publishing creates a new Catalog `QuizItem` and links back. Drafts and published items never share
  a table, so a bug in a status filter cannot leak drafts.
- Learning: `Enrollment` (learner, course run) and `Attempt`; invariant checked in one transaction: the item is
  published and belongs to a lesson of the run's course and the learner is enrolled. `Mastery` is a projection
  updated from attempts (eventually consistent, rebuilt on demand).
- Tutoring: `TutorSession` with transcript turns; never writes Learning or Catalog.

## Write ownership and integration

| Data | Owner | Others |
|---|---|---|
| courses, lessons, quiz items | Catalog | read via API / MCP |
| drafts, reviews | Authoring | quiz-gen submits generated drafts through Authoring's API |
| enrollments, attempts, mastery | Learning | tutor reads progress via MCP |
| sessions, transcripts | Tutoring | Course Ops reads for review |

Events go through a transactional outbox per module (same transaction as the change), relayed to Pub/Sub:
`item.published`, `attempt.recorded`, `learner.deleted`. Consumers are idempotent on event id. Sync reads use
timeouts of 1-2 s; if Learning is down the tutor answers without progress and says so; if Authoring is down,
quiz-gen keeps requests on its queue.

## Deployment boundaries

One Spring Boot deployable (modular monolith) with Spring Modulith modules `catalog`, `authoring`, `learning`,
`tenancy`; `ApplicationModules.of(App.class).verify()` runs in CI so a module cannot reach another's internals.
Separate services: `tutor-agent` (Python ADK, LLM latency, scales on conversation load, different failure
mode) and `quiz-gen` (Python, batch-like, Gemini quota consumer). Test for the next microservice request:
different runtime, independent scaling need, a distinct failure or compliance boundary, or a team that cannot
share a release train. Otherwise it is a module.

## Relational schema for the core contexts

One PostgreSQL schema per context (`catalog`, `authoring`, `learning`, `tutoring`), one database.

```text
catalog.course(id uuid pk, tenant_id uuid not null, slug text not null, title text not null,
               status text check (status in ('PUBLISHED','RETIRED')), unique (tenant_id, slug))
catalog.lesson(id uuid pk, course_id uuid fk, position int check (position >= 1), title text,
               unique (course_id, position))
catalog.quiz_item(id uuid pk, lesson_id uuid fk, version int, stem text, answer_index int check (answer_index >= 0),
                  published_at timestamptz not null, unique (lesson_id, id, version))
authoring.draft_item(id uuid pk, tenant_id uuid, lesson_id uuid, body jsonb, state text check (...),
                     source text check (source in ('AUTHOR','GENERATED')), published_item_id uuid null)
learning.enrollment(tenant_id uuid, learner_id uuid, run_id uuid, enrolled_at timestamptz,
                    primary key (tenant_id, learner_id, run_id))
learning.quiz_attempt(id bigint, created_at timestamptz, tenant_id uuid, learner_id uuid, run_id uuid,
                      quiz_item_id uuid, chosen_index int, correct boolean, primary key (id, created_at))
                      partition by range (created_at)
tutoring.transcript_turn(session_id uuid, turn int, tenant_id uuid, learner_id uuid, role text, text text,
                         created_at timestamptz, primary key (session_id, turn, created_at)) partition by range (created_at)
```

Indexes by query: dashboard recent activity -> `quiz_attempt (tenant_id, learner_id, run_id, created_at)`;
author review queue -> `draft_item (tenant_id, state, lesson_id)`; course lookup -> unique `(tenant_id, slug)`.

## Quiz attempts at scale and analytics

Monthly range partitions (6M rows each), created ahead by a scheduled job; local indexes per partition.
Analytics reads go to BigQuery through Datastream CDC from the replica-friendly logical stream; heavy
operational reads (exports) use the read replica. Academic retention: after 4 years a partition is exported to
the archive bucket and detached/dropped: no large DELETEs.

## Tenancy, privacy and retention

`tenant_id` on every tenant-owned row; PostgreSQL row-level security policies using
`current_setting('app.tenant_id')`, set per transaction by the API from the authenticated user; admins of one
university cannot see another's rows. Per-tenant export job by tenant_id. Learner deletion: `learner.deleted`
event, each module deletes or anonymises within 30 days (attempts anonymised where academic records require).
Transcripts: daily partitions dropped after 180 days; the agent keeps only session state in memory.

## Migration path

1. Draw module boundaries in the existing codebase; add Spring Modulith verification in report-only mode, then
   enforce. 2. Move tables into context schemas with expand-and-contract (views first, then cut over).
3. Add the outbox and the first events (`attempt.recorded`). 4. Strangle drafts: new `authoring.draft_item`,
   quiz-gen writes there, migrate DRAFT rows, then add a check constraint that `catalog.quiz_item` has no
   status other than published. 5. Partition `quiz_attempt` by creating the partitioned table and backfilling
   month by month, then swapping. 6. Enable RLS tenant by tenant, starting with the three contract customers.
Each step has a measurable check: module verification green, no cross-schema joins in pg_stat_statements,
outbox lag under 5 s, zero draft rows reachable from learner queries.
