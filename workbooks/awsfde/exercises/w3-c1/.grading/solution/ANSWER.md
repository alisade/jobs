# ANSWER: awsfde/w3-c1 Retrieval eval harness

## Approach

All callers build requests through `build_retrieve_request`, which always sets the tenant filter
from the verified tenant and ANDs user filters. A recursive check rejects any user filter on
`tenant_id`. Metrics are computed on unique documents.

## Fix

```
fixed         recall@5=0.725 mrr=0.800 leaks=1 gate=NO-GO cross-tenant results in 1 question(s); ...
hierarchical  recall@5=0.950 mrr=1.000 leaks=0 gate=GO
```

## Trade-offs / what I would do in production

Recommend hierarchical chunking: +0.225 recall@5 overall and every tenant above the floor. The leak
on q09 in the fixed index is a separate security finding: find the document, check its
`.metadata.json` sidecar and the ingestion logs, and confirm the filter code path. Run the harness in
CI on every KB change, grow the golden set from real misses, and add generation-side groundedness
evals. Twenty questions is a smoke test, not a confidence interval.
