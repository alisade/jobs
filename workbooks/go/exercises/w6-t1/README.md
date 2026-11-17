# go/w6-t1 search_kb times out after the knowledge-base backfill

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Week 6:** Agentic AI in Go (Wed RAG in Go)

## Scenario

Harbor Point runs a support agent whose main tool is `search_kb`, an MCP tool served by
`kb-retriever`, a Go service over Postgres 16 + pgvector 0.8 on RDS. This morning another
team finished backfilling Zendesk macros and a Confluence export into the shared knowledge
base (about 640k -> 2.1M chunks). Since 13:30 UTC the agent mostly answers "I couldn't
find anything", the search_kb p99 went from ~40 ms to 8-9 s, the RDS instance is at 96% CPU
and the connection pool is pinned. Nothing was deployed today. The DB on-call wants to raise
`hnsw.ef_search` and the pool size (ticket KB-231).

Start with `artifacts/PAGER.md`.

## What you have

- `artifacts/`: pager text, `\d+` and index usage stats, EXPLAIN output from prod and from
  the August benchmark, `pg_stat_statements`, service logs, pgxpool stats, an OTel trace,
  git history of the retrieval package, two tickets.
- `retrieval/`: the repository code (`repo.go`) that builds and runs the search query
  through a small `Querier` interface.
- `migrations/`: the applied schema migrations (immutable: they have run in prod).
- `retrieval/planner_test.go`: a small model of how Postgres plans this query at production
  size. `make test` replays the service's query against it.

## Task

1. Find the root cause. Explain why it became an outage only today, and whether KB-224 and
   KB-231 are related.
2. Fix it in the Go code with the smallest safe change.
3. Fill in `ANSWER.md` with the evidence (quote artifact lines) and how you would verify the
   fix in production.

## Constraints

- Do not edit `migrations/`: they are applied. A REINDEX/rebuild of the 19 GB HNSW index on
  prod was not approved this week.
- `Filter.MinSimilarity` is a public contract of the MCP tool: cosine similarity in 0..1.
- Keep every value a bind parameter; keep the tenant filter, the optional collection filter
  and the k validation.

## Acceptance criteria

- `make test` passes: the replayed query is served by the HNSW index.
- Hidden tests confirm the query ranks with an operator the index can serve, in an
  index-friendly `ORDER BY ... LIMIT` shape, that similarity scores and filters still mean
  cosine similarity, and that nothing else regressed.
- `ANSWER.md` names the root cause with evidence and addresses the red herring.

## How to run

```
make setup   # builds, prints the page
make test    # visible tests (verbose: prints the SQL and the modelled plan)
make clean
```

No database is needed.

## What to submit

Your change under `retrieval/` and `ANSWER.md`, then `/grade go/w6-t1`.

## Study-guide links

- pgvector (operators, HNSW opclasses, filtering, iterative scans): https://github.com/pgvector/pgvector
- pgvector-go: https://github.com/pgvector/pgvector-go
- Claude docs, Embeddings: https://platform.claude.com/docs/en/build-with-claude/embeddings
- Contextual Retrieval: https://www.anthropic.com/engineering/contextual-retrieval
