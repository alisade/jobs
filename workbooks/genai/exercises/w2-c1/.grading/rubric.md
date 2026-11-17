# Rubric: genai/w2-c1 Catalog service and its typed TypeScript client
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh (pytest + jest combined) |
| 2 | Pagination and query design | 10 | Full: keyset cursor on (price_cents, sku), opaque and validated, `limit + 1` to detect the last page, filters in SQL (not in Python after loading everything). Partial: works but offset inside the cursor, or filtering in memory. |
| 3 | Reservation correctness | 15 | Full: request hash stored with the key, replay returns the stored response, unique constraint on the key plus a handled race, stock check and decrement in one transaction; ANSWER.md says how it would hold on Postgres under concurrency (conditional UPDATE or row lock). Partial: idempotent in tests but racy by design without acknowledging it. |
| 4 | Contract discipline | 15 | Problem model declared per response, explicit operation ids, generated types committed and never edited, client built on generated types (no duplicated hand-written interfaces), `make contract` in the workflow; mentions a CI check that fails on drift. |
| 5 | ANSWER.md | 10 | Clear trade-offs: keyset vs offset, key retention and expiry, versioning of the contract, who owns the generated client. |
Total: 100
