# javaai/w1-t1 - The learner dashboard got slow after a "small" release

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 1 (Wed: Spring Data JPA, fetch plans, the N+1 problem; Fri: performance and indexes)

## Symptom

Kestrel Learning's `progress-api` (Spring Boot 3.5, Spring Data JPA, Cloud SQL for PostgreSQL on
Cloud Run) serves the learner dashboard and the tutor agent's `get_learner_progress` tool. The day
after release 0.9.0 ("dashboard shows per-lesson progress for every enrolled course"), semester
start traffic arrived: p95 went from 110 ms to 4 s, Cloud SQL CPU hit 98%, and requests began
failing with HikariCP "Connection is not available". L2 wants to raise the pool size from 10 to 50
and Cloud Run max instances from 4 to 12. Start with `incident/PAGE.txt`.

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt` | the incident and its work notes |
| `incident/app-log-excerpt.txt` | request logs with Hibernate session metrics, Hikari errors, a SQL sample |
| `incident/metrics.txt` | Cloud Run, Cloud SQL and Query Insights numbers |
| `src/main/java/com/kestrel/progress/` | the service (entities, repositories, `ProgressService`) |
| `src/main/resources/` | `application.properties`, Flyway `V1__progress.sql` |
| `src/test/java/.../Seed.java`, `ProgressVisibleTest.java` | test data builder and a visible test |

H2 in PostgreSQL mode stands in for Cloud SQL. `hibernate.generate_statistics` is on, as in
production, so you can count statements in a test.

## Your task

1. Find the root cause and prove it from the bundle and by reproducing it locally (count the
   statements one request runs for a learner with many courses).
2. Decide whether the pool-size and max-instances proposal is a fix, a mitigation or harmful, and say why.
3. Fix it: the number of SQL statements per request must be a small constant (at most 4) that does
   not grow with courses, lessons or attempts, with exactly the same JSON as today (ordering,
   lessons with no attempts, other learners' attempts not counted). Make sure the query that
   replaces the loop is served by an index (new Flyway migration; do not edit V1).
4. `make test`, then write `ANSWER.md`: Approach, Root cause (with evidence), Fix and how you
   verified it, Trade-offs / production follow-ups (how you would catch this before release).

## Acceptance criteria (what the grader checks)

- Statement count per request bounded and independent of data size (Hibernate statistics).
- Response unchanged for small and large learners, including empty learners.
- Pool size not raised; an index that starts with `quiz_attempt.learner_id` exists.
- Root cause and evidence in `ANSWER.md` match the incident.

## How to run

```bash
make setup
make test
# from workbooks/: /grade javaai/w1-t1
make clean
```
