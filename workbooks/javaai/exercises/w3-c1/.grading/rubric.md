# Rubric: javaai/w3-c1 Quiz generation with Gemini structured output: validate, retry, back off
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Loop design | 15 | One bounded loop with separate budgets for validity attempts and rate-limit retries, a deadline checked before every sleep, no recursion, no exception escaping; Blocked short-circuits. Partial: correct behaviour but tangled control flow or duplicated request building. |
| 3 | Validation and feedback | 10 | Specific, item-numbered messages that a model can act on; schema and validator responsibilities clearly separated (schema for shape, validator for meaning: grounding, giveaways, uniqueness). |
| 4 | Backoff correctness | 5 | Full jitter with a cap, Retry-After as a floor, no sleep past the deadline. |
| 5 | Production judgement in ANSWER.md | 15 | Explains why schema-constrained output still needs validation (schemas do not express grounding or giveaways; truncation), how Blocked vs Failed surfaces to the learner and to metrics, cost of retries (each corrective retry pays input tokens again), PayGo 429 vs Provisioned Throughput, model version pinning, token logging per request. |
| 6 | Code quality | 5 | Records and sealed results used idiomatically, small private helpers, no magic numbers outside config. |
Total: 100
