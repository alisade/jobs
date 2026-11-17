# Rubric: ms/w2-c1 Eventhouse KQL pack for fleet telemetry
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Update policy design | 15 | Full: function output exactly matches the target schema, bad rows filtered, policy transactional and the ANSWER explains why (failed transform fails ingestion, no silent loss). Partial: correct but no reasoning. Zero: non-transactional or schema mismatch. |
| 3 | Materialized view correctness | 10 | Full: valid view (single trailing summarize, no now()), backfill with async, lookback justified against retry timing. Partial: valid but lookback unjustified. Zero: query a view cannot accept. |
| 4 | Session/trip logic | 10 | Full: correct per-vehicle restart, ascending order, dedupe before sessionizing, matches the expected trips table. Partial: right function, wrong order or no restart. |
| 5 | Query quality | 5 | Filters before summarize, no take/limit in production queries, readable aliases. |
| 6 | Trade-offs in ANSWER.md | 10 | Full: compares update policy vs Eventstream processing vs notebook, view vs query-time dedupe, and how to test KQL before deploy. Partial: one of these. Zero: missing. |
Total: 100
