# ANSWER: genai/w6-t1 Holiday peak: the assistant says "in stock" for sold-out items

## Approach

<!-- Which evidence you read first, how you lined up the log with the inventory audit trail, what make demo showed. -->

## Root cause

<!-- The mechanism with quoted log lines: the cache key, the TTL, what gets cached. Why 087, why 012 after
lunch, how the order status leaked, and why the replication lag is or is not involved. -->

## Fix

<!-- What you changed and how you verified it. -->

## Trade-offs / what I would do in production

<!-- Short. Caching by data class, where the class comes from (tools used), semantic caches, what to tell
privacy, purge of the bad entries, a test for "no personal data in shared caches", peak-readiness review. -->
