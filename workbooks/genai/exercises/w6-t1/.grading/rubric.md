# Rubric: genai/w6-t1 Holiday peak: the assistant says in stock for sold-out items
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (several guards pass on the starter) |
| 2 | Root cause identified | 25 | Full: the answer cache keys only on the normalized question text, with a 24 h TTL, and caches every answer. Answers that depended on live inventory (scoped to a store and fresh for minutes) and on customer data (scoped to one user) are served to anyone who asks the same words. So 087 got 012's 08:00 answer, 012 kept the 08:00 answer after the stock sold out at 11:58, and u-ben got u-ana's order. Partial (10-15): "the cache is stale" without the key/scope mechanism or without the personal-data leak. Zero: blames inventory or the model. |
| 3 | Evidence | 20 | Full: quotes the 18:00 log line (store_id 087, cache_hit true, answer naming store 012), the 13:00 hit after the 11:58 sale, the u-ben hit on `where is my order` returning K-1001, the cache key and `cache_all_answers: true`, and the "1 inventory API call today". Partial: one or two. |
| 4 | Red herring ruled out | 5 | The lag was 07:52-07:56. The only inventory read was at 08:00 and returned the true value of 6. Every wrong answer is a cache hit with no inventory call, and the API returns 0 now. |
| 5 | Fix quality | 10 | Classifies by the tools used (most sensitive wins), scopes or skips volatile answers, never caches personal, keeps FAQ global 24 h, catalog 1 h; no change to the fake agent. |
| 6 | Prevention | 10 | Concrete: purge the bad entries, notify privacy (scope: which users could have seen which orders), a test that no personal data is stored in a shared cache, cache policy reviewed per data class before peak, show "as of" times on stock answers, alarm on stock-answer hit rate. Partial: generic. |
Total: 100
