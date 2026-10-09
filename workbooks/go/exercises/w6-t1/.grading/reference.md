# Reference: go/w6-t1 search_kb times out after the knowledge-base backfill

## Root cause

Commit b71e0aa (#412, shipped in v1.14.0 on 2026-09-24) "unified" the distance expression
into one const and, while doing so, changed the operator from `<=>` (cosine distance) to
`<->` (L2 distance). The only ANN index, `kb_chunks_embedding_hnsw`, is built with
`vector_cosine_ops`, which serves `ORDER BY embedding <=> $1 LIMIT n` only. With `<->`
the planner has no index that can produce rows in that order, so it does a Parallel Seq
Scan over the whole table plus a top-N heapsort.

Evidence chain:

- `explain-prod-2026-10-06.txt`: `Sort Key: ((embedding <-> ...))`, `Parallel Seq Scan on
  kb_chunks`, `Buffers: ... read=1062211`, 8.8 s.
- `psql-describe-kb_chunks.txt`: `hnsw (embedding vector_cosine_ops)`; `last_idx_scan` for the
  HNSW index is 2026-09-24 09:09:51, the minute v1.14.0 rolled out, while every other index
  is still being scanned today.
- `explain-staging-2026-08-14.txt`: the same query with `<=>` uses `Index Scan using
  kb_chunks_embedding_hnsw`, 5 ms.
- `pg_stat_statements.txt` and `git-log-retrieval.txt`: the running statement text uses
  `<->`; #412 claimed "no behaviour change intended".

Why only today: a seq scan's cost is linear in table size. At 640k rows it was a few hundred
ms (log line at 13:27, 412 ms): slow but under the 3 s `statement_timeout`. At 2.1M rows it
is ~9 s, every call hits the timeout, connections are held for 3 s each, the 10-connection
pool saturates (acquire waits, `context deadline exceeded`), and RDS CPU pegs.

KB-224 is the same bug, seen earlier: the Go code computes similarity as `1 - distance`. With
L2 distance on normalised vectors, `d = sqrt(2 - 2cos)`, so cosine 0.76 shows up as 0.31 and
the agent's 0.72 threshold silently drops good hits.

Red herring: KB-231. `hnsw.ef_search` only affects HNSW index scans, which are not
happening, and a bigger pool just runs more concurrent seq scans on a CPU-bound instance.

## Fix

`retrieval/repo.go`: `const distanceExpr = "c.embedding <=> $1"`. Everything else stays: the
ORDER BY is the bare ascending distance expression with `LIMIT $3`, similarity is
`1 - cosine distance`, migrations untouched. See `.grading/solution/retrieval/repo.go`.

Verify in prod: canary the image, then `EXPLAIN (ANALYZE, BUFFERS)` shows `Index Scan using
kb_chunks_embedding_hnsw`, `pg_stat_user_indexes.idx_scan` for the HNSW index climbs again,
p99 back near 40 ms, pool acquire waits gone. Reset `pg_stat_statements` to see the new
statement cleanly.

## Production follow-ups a strong answer mentions

- Guard rail: a CI test that runs EXPLAIN against a seeded Postgres (testcontainers) and
  fails on `Seq Scan on kb_chunks`, or at least a unit test pinning operator to opclass.
  Alert on `idx_scan` of the HNSW index not increasing.
- Name the metric in the type system: a `Distance` type per metric, or derive the operator
  from one config value shared with the migration generator.
- Filtered ANN recall: HNSW scans ef_search candidates, then the tenant filter runs, so a
  small tenant on a big shared index can get fewer than k rows. Options: pgvector 0.8
  `hnsw.iterative_scan`, partial indexes per large tenant, or partitioning by tenant.
- Load-shedding on the tool: a short per-call timeout and a circuit breaker so a slow DB
  does not pin every agent turn for 10 s.
