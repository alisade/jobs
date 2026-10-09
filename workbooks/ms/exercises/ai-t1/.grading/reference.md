# Reference: ms/ai-t1

## Root cause

Release 2026.12.1 rebuilt the index with embedder `hash-bow-v2`
(`incident/index-manifest-2026-12-07.json`: `"embedder": "hash-bow-v2"`), but the query path
config was not changed (`incident/app-config-deployed.yaml`: `query_embedder: hash-bow-v1`). Both
embedders produce 1024-dimension vectors, so nothing errors; the query vector and the chunk
vectors live in unrelated spaces and cosine similarity is noise. Hit rate drops from 1.0 to
0.417, which is roughly what random ranking of 10 documents with top-3 gives.

Evidence that points straight at it: top-1 scores collapse from about 0.35-0.47
(`eval-2026-11-24.json`) to about 0.03-0.07 (`query-log-2026-12-07.jsonl`, `eval-2026-12-07.json`).
Smaller chunks would shift scores, not erase them.

## Red herring: chunk size 200 -> 120

Build a v1 index at chunk 120 and query with v1: hit rate stays 1.0. Build the v2 index at 200
and query with v1: still 0.417. Chunk size is irrelevant to this failure.

```
uv run python -c "from policy_rag.index import build_index as b; from policy_rag.retriever import Retriever as R; from policy_rag.evaluate import evaluate as e; b('corpus','/tmp/i','hash-bow-v1',120,20); print(e(R('/tmp/i','hash-bow-v1'),'eval/questions.jsonl')['hit_rate'])"
```

## Fix

- `config/app.yaml`: `query_embedder: hash-bow-v2`.
- `Retriever.__init__`: compare `manifest["embedder"]` with the configured query embedder and
  `manifest["dims"]` with the embedder's dims; raise `IndexMismatchError` naming both sides. See
  `.grading/solution/policy_rag/retriever.py`. An alternative design reads the embedder from the
  manifest and drops the setting; still keep a check that the deployed code knows that embedder.

## Production

- Version the index and its query configuration as one artifact; never deploy one without the
  other. Write the embedding model and version into the index metadata (here the manifest).
- Azure AI Search: point the embedding skill and the vectorizer at the same model deployment
  (Microsoft: "You must use the same embedding model for both"); the import wizard does this by
  design. Changing the model means a new vector field or a new index and a re-index, then a
  swap via an alias or app setting, with the eval gate in between.
- Run the retrieval eval in the release pipeline as a gate, not only nightly; alert on top-1
  score distribution drift as well as hit rate.

## Interview angles

- Why did no error fire? (Same dims. A dims mismatch is the loud failure; a model mismatch at
  equal dims is the silent one.)
- How would you do a zero-downtime embedding-model migration in Azure AI Search?
- What eval size makes a 0.8 threshold meaningful, and how do you keep the eval set from going
  stale as the corpus changes?
