# Release 2026.11 (policy retrieval)

- Chunker v2: fixed-size 60-word windows with 10-word overlap, so every chunk has the same size and the
  embedding batch job is predictable (replaces v1 per-section chunks of uneven size).
- Embedding model upgraded to the next stable version; index rebuilt (blue-green swap, index v14 -> v15).
- Reranker top-N raised from 20 to 30.
- Dashboard: new "chunks per policy" panel.
