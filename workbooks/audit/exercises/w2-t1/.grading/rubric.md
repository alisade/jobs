# Rubric: audit/w2-t1 The CM-03 population does not reconcile: 38 vs 421
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 25 | Full: the client treats a page shorter than the requested per_page as the last page; the server caps per_page at 50 (the GHE configuration), so page 1 returns 50 < 100 items and the loop stops after one request; the Link rel="next" header was there and ignored. Partial: "pagination bug" without the cap interaction. Zero: time zone or token scope. |
| 3 | Evidence | 15 | Full: quotes the debug line showing per_page=100 requested, 50 items returned, Link with per_page=50&page=2 rel="next", and "1 request(s)"; shows 488 closed PRs exist after the fix. Partial: asserts without the log. |
| 4 | Fix quality | 15 | Full: follows Link rel="next" until absent; no dependence on page size; bounded (max pages and loop detection); duplicate detection; time-zone code untouched. Partial: lowers per_page to 50 (fragile, would break again on the next config change). |
| 5 | Red herrings and IPE note | 10 | Full: rules out time zone (boundary dates correct, and a TZ issue would move a handful of items, not 383), token scope (no 403s, 200 on every call), and explains the upgrade's role (it lowered the cap and exposed the bug, it is not the bug); auditor note covers re-extraction, query and parameters, and a reconciliation-to-control-total check that fails the job on mismatch. |
Total: 100
