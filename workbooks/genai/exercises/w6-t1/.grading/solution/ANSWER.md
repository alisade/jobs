# ANSWER: genai/w6-t1 Holiday peak: the assistant says "in stock" for sold-out items

## Approach

I read the conversation log next to the inventory audit trail. Then I ran `make demo`, which reproduced
all three symptoms: the stale 012 answer, the cross-store 087 answer and the order leak.

## Root cause

The answer cache keys on the normalized question alone (`key: normalize(question)`), keeps entries for
24 h, and caches every answer (`cache_all_answers: true`). Stock and order answers are cached and shared
across stores and users like FAQs.
- 18:00 log line: `"store_id": "087", "cache_hit": true, "cache_key": "is the glacier 45 cooler in stock",
  "answer": "... in stock (6 left) at store 012."` The answer names another store.
- 13:00 at 012: `cache_hit: true` with the 08:00 answer, but the audit trail shows the last unit sold
  at 11:58.
- 15:20 u-ben: `"cache_key": "where is my order", "cache_hit": true, "answer": "Order K-1001 ..."`. That
  is u-ana's order.
- The inventory API was called once all day (08:00, store 012), and it returned the correct 6.

The replication lag (07:52-07:56) is unrelated. It ended before the only inventory read, which was
correct, and every wrong answer is a cache hit with no tool call.

## Fix

`cache.py` now classifies answers by the tools they used. Personal answers are never cached. Stock
answers are keyed per store with a 60 s TTL. Catalog answers are global for 1 h, and FAQ answers are
global for 24 h. After the fix, `make demo` shows correct stock for 012 at 13:00 and 087 at 18:00, a
miss for u-ben, and FAQ hits unchanged. Tests pass.

## Trade-offs / what I would do in production

- Purge Redis now. Send privacy the users who got cached personal answers since 11/20.
- Add a test that personal data never goes into a shared cache, and review cache policy per data class
  before peak.
- Stock answers should show "as of" times.
- A semantic cache makes this worse, not better, unless the same rules apply.
