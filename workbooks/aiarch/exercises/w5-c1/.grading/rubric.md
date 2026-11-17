# Rubric: aiarch/w5-c1 One table for Lighthouse platform state
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Data model | 15 | Access-pattern-first table; Query not Scan; GSI overloading or a justified second GSI; TTL in epoch seconds. |
| 3 | Correctness under retries and concurrency | 10 | Conditional writes, claim removed on failure, in-progress handled, optimistic locking with state check. |
| 4 | Code quality | 5 | Expression attribute names, integer money, small functions. |
| 5 | ANSWER.md | 15 | Key table, Memory vs table boundary argued, hot partition and leading-key IAM, Streams for the ledger. |
Total: 100
