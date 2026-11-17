# javaai/w6-t1 - The dashboard's Recent activity card got slow as data grew

**Type:** troubleshooting | **Estimate:** 1-1.5 hours | **Study plan:** Week 6 (Thu: indexes, EXPLAIN and composite index order; Fri: migrations at scale)

## Symptom

The learner dashboard's "Recent activity" card takes 1.5-4 s and Cloud SQL CPU is 80-90% at peak.
The query has not changed since July; quiz attempts doubled since semester start (41M rows). The DBA
ran VACUUM ANALYZE and suggested bigger buffers; nothing changed. Start with `incident/PAGE.txt`.

SQLite stands in for Cloud SQL for PostgreSQL: same schema, same migration discipline, and the
same plan shapes for this query (`EXPLAIN QUERY PLAN` instead of `EXPLAIN ANALYZE`).

## What you have

| Path | What it is |
|---|---|
| `incident/` | page, Query Insights and a PostgreSQL plan |
| `dashboard/queries.py` | the query |
| `dashboard/db.py` | the migration runner (checksums applied migrations; do not change) |
| `migrations/V1..V6` | applied in production; never edit them |
| `scripts/seed.py`, `make explain` | a 200k-row local copy; plan and timing |

## Your task

1. Find the root cause and prove it: read both plans, explain why the existing index does not help
   and what it is doing instead.
2. Rule VACUUM/ANALYZE and buffer sizing in or out with evidence.
3. Fix it with a new migration (V7 or later, additive) and, if needed, a query change that returns
   exactly the same rows. Show the plan before and after (`make explain` applies new migrations to
   your local copy).
4. `make test`, then write `ANSWER.md` (Approach, Root cause with evidence, Fix and verification,
   Trade-offs / production follow-ups).

## Acceptance criteria (what the grader checks)

- V1-V6 byte-identical; a new additive migration exists.
- The plan searches quiz_attempt by an index on learner_id and course_id with the created_at range,
  with no temporary sort.
- Results identical to the original semantics, including the inclusive boundary day.
- Root cause and evidence in `ANSWER.md` match the incident.

## How to run

```bash
make setup     # venv + data/kestrel.db (200k attempts)
make explain   # plan and ms per query, before and after
make test
# from workbooks/: /grade javaai/w6-t1
make clean
```
