# Reference: awsfde/w3-c1

Solution files: `.grading/solution/kb_eval/request.py` and `harness.py`.

- **One builder, filter always on.** The tenant filter comes from the verified tenant (token claim),
  never from the question or a tool argument. User filters are ANDed; an `orAll` from the user stays
  inside the `andAll`, because `orAll: [tenant, doc_type=sop]` would return every tenant's SOPs.
  `andAll` and `orAll` require at least two members in the Retrieve API model, so a single filter is
  sent bare. Rejecting `tenant_id` in user filters closes the "notEquals my tenant" trick.
- **Documents, not chunks.** The KB returns chunks; hierarchical chunking in particular returns
  several chunks of one parent. Recall and MRR over raw chunks overstate quality.
- **Leaks are not a metric.** One cross-tenant chunk is a security incident, so the gate fails on any
  leak regardless of recall. A missing `tenant_id` is treated as a leak because an untagged document is
  exactly how the filter gets bypassed in practice (metadata sidecar missing or misnamed at ingestion).
- **Numbers on the fixtures:** fixed recall@5 0.725, MRR 0.80, one leak (q09); hierarchical recall@5
  0.95, MRR 1.0, no leaks; hierarchical is GO. The leak in the fixed recording should still be
  investigated on its own: it says the old index has an untagged or wrongly tagged document.

Production: run the harness in CI on any change to chunking, embedding model, parsing or filters;
grow the golden set from real misses; report confidence (20 questions is a smoke test); add
generation-side evals (groundedness, citation correctness) separately from retrieval.
