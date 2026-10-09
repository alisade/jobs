# ms/ai-t1 answer (model)

## Approach
Started from what changed (release notes: new embedder v2 and chunk size 200 -> 120), then
compared the index manifest with the deployed app config, then tested each change in isolation by
building indexes into /tmp and running the eval.

## Root cause
The index was rebuilt with embedder hash-bow-v2, but the query path still embeds questions with
hash-bow-v1.
- `incident/index-manifest-2026-12-07.json`: `"embedder": "hash-bow-v2", "dims": 1024`
- `incident/app-config-deployed.yaml`: `query_embedder: hash-bow-v1`
Both are 1024-dim, so nothing failed; similarities became noise. Top-1 scores fell from ~0.4
(`eval-2026-11-24.json`, q01 0.4587) to ~0.04 (`query-log-2026-12-07.jsonl`, PTO question
0.0366 citing benefits-enrollment#0). Hit rate 1.0 -> 0.417.
Chunk size is not the cause: v1 index at chunk 120 queried with v1 -> 1.0; v2 index at chunk 200
queried with v1 -> 0.417.

## Fix
- config/app.yaml: query_embedder hash-bow-v2. `make eval` -> hit_rate=1.0.
- Retriever refuses to start on embedder name or dims mismatch with IndexMismatchError naming
  both sides; verified it raises for v1-on-v2 and passes for v2-on-v2 and v1-on-v1.

## Trade-offs / what I would do in production
Ship index + query config as one versioned artifact; gate releases on the retrieval eval; in
Azure AI Search keep the embedding skill and vectorizer on the same model deployment and migrate
models via a new vector field or index plus re-index and swap; alert on score drift too.
