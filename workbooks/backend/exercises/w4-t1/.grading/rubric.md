# Rubric: backend/w4-t1 Sales managers see someone else's account names in the pipeline view
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (three visible tests are guards that pass on the starter) |
| 2 | Root cause | 30 | Full: the DataLoader is process-wide (module scope), so (a) its cache, keyed by an id that is only unique per tenant, serves another tenant's row and never expires, and (b) the batch function uses a module-level auth set by the latest request, so batches run under the wrong identity. Partial: "caching bug" without the per-request lifetime or the auth race. Zero: CDN or accounts-svc. |
| 3 | Evidence | 15 | Quotes the repro output, the query-log lines where a batch's tenant differs from the request's, the git log of KEY-2410, and the edge team's no-store/pass-through evidence. |
| 4 | Fix | 15 | Loaders created per request in the context factory with auth captured in the batch function; batching preserved; no tenant-blind cross-request cache. Partial: tenant added to the cache key but loader still global (fixes the cache, not the auth race). |
| 5 | Prevention and follow-up | 10 | Interleaved multi-tenant test, a lint or review rule for module-level loaders, treat as a cross-tenant disclosure with a scoping query over logs (including agent transcripts). |
Total: 100
