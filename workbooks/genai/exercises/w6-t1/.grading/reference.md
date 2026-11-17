# Reference: genai/w6-t1

## Root cause
`AnswerCache.key()` returns only `normalize(question)`, `TTL_S` is 24 h, and `Assistant.ask` caches
every answer (`cache_all_answers: true`). The cache ignores what the answer depended on:
- **Stock** depends on the store and on the time. Store 012's 08:00 answer ("in stock (6 left) at store
  012") was served at 13:00, after the last unit sold at 11:58. At 18:00 store 087 got the same answer,
  still naming store 012. The log shows `cache_hit: true` and `tools: []` for both.
- **Orders** depend on the user. u-ben's `where is my order` hit u-ana's cached answer (K-1001). That is
  a privacy incident.
- The inventory API was called once all day (08:00, store 012), and that call returned the true value.

Red herring: the replica lag (07:52-07:56) ended before the only inventory read, and the API is correct
now. Every wrong answer came from the cache.

## Fix (solution/assistant/cache.py)
Classify each answer by the most sensitive tool it used: personal is never cached; volatile is keyed
with the store and lives 60 s; catalog is global for 1 h; static (FAQ) is global for 24 h. `get` checks
the global key and the store-scoped key.

## Prevention
- Purge the cache. Give privacy the list of users with cache hits on personal answers since 11/20 and
  which orders they could have seen.
- Add a test that personal data never lands in a shared cache. Assign a cache policy per data class and
  review it before peak.
- Stock answers should carry an "as of" time and say "check the shelf" when stock is low.
- Alarm when the stock-answer hit rate is above 0.
