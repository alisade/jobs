# go/w6-t1 ANSWER (model)

## Approach

Started from the trace: the time is all in the `SELECT kb` span, which ends in SQLSTATE
57014 at 3 s, so the DB is slow and the pool exhaustion is a consequence. Read the prod
EXPLAIN next, compared it with the August staging EXPLAIN, then checked index usage stats
and the git log for when the plan could have changed.

## Root cause

The search query ranks by `<->` (L2) but the only HNSW index is `vector_cosine_ops`, which
can only serve `<=>`. The planner cannot use it and falls back to a full scan.

- prod EXPLAIN: `Sort Key: ((embedding <-> '[...]'::vector))` over `Parallel Seq Scan on
  kb_chunks c`, `read=1062211`, `Execution Time: 8802.731 ms`.
- staging EXPLAIN with `<=>`: `Index Scan using kb_chunks_embedding_hnsw`, 5.4 ms.
- `\d+ kb_chunks`: `hnsw (embedding vector_cosine_ops)`.
- `pg_stat_user_indexes`: HNSW `last_idx_scan = 2026-09-24 09:09:51`, which is the v1.14.0
  rollout; commit b71e0aa (#412) changed the const to `<->`.

It became an outage today because the seq scan cost scales with rows: 640k -> 2.1M pushed
every search past the 3 s statement_timeout, connections were held for the full 3 s and the
pool of 10 saturated. KB-224 is the same bug: `1 - L2 distance` is not cosine similarity, so
the 0.72 threshold dropped relevant hits since 2026-09-24.

## Fix

`retrieval/repo.go`: `distanceExpr = "c.embedding <=> $1"`, with a comment tying it to the
index opclass. `make test` now shows `Index Scan using kb_chunks_embedding_hnsw`. In prod:
canary, EXPLAIN shows the index scan, HNSW `idx_scan` increases, p99 and pool waits recover.

## Trade-offs / what I would do in production

- Do not do KB-231: ef_search affects only index scans, and a bigger pool means more
  concurrent seq scans on a CPU-bound instance.
- Add a CI EXPLAIN check against a seeded Postgres and an alert on HNSW idx_scan flatlining.
- Tenant filter after HNSW can return fewer than k: enable `hnsw.iterative_scan` or add
  partial indexes for large tenants.
- Revert the agent's min_similarity workaround from KB-224 once fixed.
