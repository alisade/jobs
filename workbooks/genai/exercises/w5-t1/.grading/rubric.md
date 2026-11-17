# Rubric: genai/w5-t1 Assistant answers time out at peak while the model looks slow
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (a few guards pass on the starter) |
| 2 | Root cause identified | 25 | Full: release 2026.11.18 made `check_inventory` look up every product in the answer, one GET per (sku, store) pair, awaited one after another (N+1, sequential), with a 2 s per-call timeout and no overall deadline. 20 SKUs x 2 stores = 40 serial calls; at peak catalog p50 0.7 s that is 28 s of tool time on top of two 2.2 s model calls, past Kong's 30 s route timeout. Short questions call few or no products; off-peak catalog is 0.18 s so 40 calls fit. Partial (10-15): "catalog is slow" or "too many calls" without the sequential fan-out and missing deadline. Zero: blames the model provider. |
| 3 | Evidence | 20 | Full: from the slow trace, about 35 sequential `GET /inventory/{sku}` spans under `execute_tool check_inventory` (start times back to back, 0.6-1.2 s each) and the tool span running to the 30 s cut; the normal trace's 6 catalog calls (3 SKUs x 2 stores) totalling about 1 s; catalog latency at 16:40-17:00 vs 09:00; the assistant log `completed_lookups=35/40`; calls per turn 6 to 31. Partial: one or two of these. |
| 4 | Red herring ruled out | 5 | The model spans are the longest single spans, but the sum of catalog spans dominates the slow trace; provider B would save at most a second or two of 30. Catalog is within its own SLO; the caller multiplied its latency. |
| 5 | Fix quality | 10 | Batch endpoint with chunks of 50, a semaphore cap, the deadline computed once and each call's timeout min(per-call, remaining), partial results instead of raising, order preserved and duplicates removed; does not edit the client. |
| 6 | Prevention | 10 | Concrete: deadline propagation from the gateway budget (header or context) through the agent loop to every tool, a call-count/latency budget per tool asserted in tests or traces, load test of the tool at peak latency, UX for "stock unknown", an alert on tool span duration. Partial: generic "load test". |
Total: 100
