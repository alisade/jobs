# Rubric: connect/w5-t1 The help desk bot quotes HR-only and retired articles
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (several are guards that already pass) |
| 2 | Root cause identified | 25 | Full: trigger = exporter 2026.10.05 renamed the sidecar key department -> dept, so the retriever's orAll branch `equals department` matches nothing; only department-restricted articles depended on it, so Finance/HR/Legal callers got zero filtered results while all-employees content still matched (why IT looked fine). Latent defect = HD-2231 unfiltered fallback (since 2026.09.22) re-ran Retrieve with no filter at all, dropping audience, region and status - hence other departments' and retired articles. Partial (10-15): only one of the two. Zero: blames the model, ingestion failures or embeddings. |
| 3 | Evidence | 20 | Full: quotes retrieval log lines (filteredCount 0 + fallback unfiltered for Finance/HR/Legal), a sidecar showing dept, the diff, dashboard jump in filtered=0 rate on 10-06; explains that a filter on a missing key is not an error in Bedrock KB filtering, it matches nothing. Partial: one piece. |
| 4 | Red herring and blast radius | 10 | Rules out the 3 ingestion failures (attachments over the 10 KB metadata limit, present on both days); lists which callers saw which forbidden articles from the log and since when (exporter ran 2026-10-06 02:00). |
| 5 | Fix and prevention | 15 | Full: exporter writes department again (or a schema-driven mapping) with a schema check; retriever fails closed (hand off, never unfiltered); schema file unchanged; proposes a contract test in both pipelines, an alarm on filtered=0 rate, and considers Managed KB ACL crawl. Partial: only one side fixed. Zero: retriever switched to dept and fallback kept. |
Total: 100
