# genai/w6-t1 - Holiday peak: the assistant says "in stock" for sold-out items

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 6 (retail risks: wrong stock
or prices shown as fact, peak traffic); Week 3 (caching and cost)

## Symptom

On Black Friday, store associates at two Kestrel stores report that the assistant gives stock answers
that are wrong, and privacy heard that a customer saw someone else's order status. Read
`evidence/PAGE.md` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/PAGE.md` | the page and the thread |
| `evidence/conversation-log.jsonl` | assistant request log with cache flags, keys, tools and answers |
| `evidence/inventory-api.txt` | live inventory API responses and the audit trail |
| `evidence/cache-config.yaml`, `evidence/release-notes.md` | the cache that shipped on 11/20 |
| `evidence/alerts.txt` | the inventory replication lag alert |
| `assistant/cache.py` | the answer cache |
| `assistant/pipeline.py` | cache, then agent |
| `assistant/backend.py` | fake inventory, orders and a deterministic agent (complete; do not change it) |
| `scripts/demo.py` | `make demo` replays the day |

## Your task

1. Find the root cause with evidence: why store 087 got store 012's morning answer, why 012 got a stale
   answer after lunch, how the order status leaked, and whether the replication lag played any part.
2. Fix `assistant/cache.py` (and `pipeline.py` if you need to) so that:
   - an answer that used `check_inventory` is never served to another store and is never older than
     60 s (not caching it at all is also acceptable);
   - an answer that used customer data (`get_order_status`) is never cached;
   - catalog answers (`search_products` only, such as prices) are cached for at most 1 h;
   - FAQ and policy answers (no tools, or `policy_lookup`) are still cached for 24 h across users and
     stores, with the same normalization, so the holiday hit rate holds.
3. Verify with `make demo` and `make test`.
4. Write `ANSWER.md`: Approach, Root cause (with evidence), Fix (and verification), Trade-offs / prevention.

## Acceptance criteria (what the grader checks)

- Per-store and freshness rules for stock answers; personal answers never cached or shared.
- FAQ caching and hit rate preserved; catalog TTL respected.
- `ANSWER.md` names the mechanism with quoted log lines and rules out the replication lag.

## How to run

```bash
make setup
make demo
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade genai/w6-t1
make clean
```
