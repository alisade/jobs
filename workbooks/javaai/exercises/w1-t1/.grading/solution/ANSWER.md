# ANSWER: javaai/w1-t1 The learner dashboard got slow after a small release

## Approach

Read the page, then the metrics: stmt_per_req jumped from 1.8 to about 74 with release 0.9.0 and
Cloud SQL CPU followed the request rate. The Hikari errors only start at 09:05, after CPU passed
95%, so they are downstream. Read ProgressService and reproduced locally with Seed (8 courses x 15
lessons) and Hibernate statistics.

## Root cause

N+1 queries from lazy associations in nested loops: 1 enrollment query, then per course a lazy
course load and a lazy lessons load, then one attempts query per lesson. Evidence: session metrics
"preparing 131 JDBC statements" (lrn-20817), 64 and 157 for others, 1 for a learner with no
enrollments; the SQL sample repeats `select ... from quiz_attempt ... where learner_id=? and l1_0.id=?`;
Query Insights shows 1.9M calls of that query, each a Seq Scan of 4.1M rows because quiz_attempt has
no learner_id index. Locally: 1 + 2*8 + 120 = 137 statements for one request.
The pool exhaustion is a consequence: slow transactions hold connections. Raising the pool to 50 on
12 instances (600) against max_connections 100 would fail in the database instead.

## Fix

Fetch-join query for enrollments, course and lessons; one grouped aggregate for attempts per
lesson; lessons sorted by position; V2 migration with an index on (learner_id, lesson_id, correct).
Locally the request now runs 2 statements for both small and large learners; all tests pass.

## Trade-offs / what I would do in production

Ship the index with CREATE INDEX CONCURRENTLY first, then the code. Add a CI test that asserts
statement counts for a large learner, and an alert on calls per normalized query. If the dashboard
grows, move to a precomputed progress read model. Keep the pool at 10.
