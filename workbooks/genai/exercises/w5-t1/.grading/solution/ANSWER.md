# ANSWER: genai/w5-t1 Assistant answers time out at peak

## Approach

The page says the model spans are the longest, so I first compared the sum of spans per phase in both
traces instead of the single longest span. Then I matched the release note and the catalog call counts,
and reproduced the problem with `make demo`: 12 s off peak, a gateway timeout at peak, 40 single calls
in both.

## Root cause

Release 2026.11.18 made `check_inventory` cover every product in the answer: 20 SKUs x 2 stores.
The tool awaits one `GET /inventory/{sku}` per pair, sequentially, with a 2 s timeout per call and no
overall deadline. At peak each call takes about 0.7 s, so the tool alone needs about 28 s and the
request passes Kong's 30 s timeout.
- Slow trace: 35 back-to-back catalog spans of 0.61-1.18 s under `execute_tool check_inventory`. The
  tool span runs until 30,000 ms, then the root span returns 504.
- Normal trace: 6 catalog spans (3 SKUs x 2 stores), tool 1.1 s. The longest span is the model at 2.3 s.
- Catalog: calls per turn went from 6 to an average of 31 (max 40), and p50 went from 0.16 s at 09:00
  to 0.71 s at 17:00.
- Assistant log: `phase=tool check_inventory; skus=20 stores=2 completed_lookups=35/40`.

Short questions use few or no products. Off peak, 40 x 0.18 s still fits. Switching provider would save
at most about 1-2 s of the 30 s, so it would not fix this. Catalog is inside its own SLO: the caller
multiplied its latency 40x.

## Fix

The tool now uses `batch_stock` (chunks of 50) behind a semaphore of 4. It computes one deadline from
`deadline_s`, uses a per-call timeout of min(0.8 s, remaining), and returns partial results with
`stock_unknown` instead of raising. With the fix, `make demo` shows 4.6 s off peak and 5.1 s at peak,
with one batch call, and all tests pass.

## Trade-offs / what I would do in production

- Batching depends on the catalog batch endpoint's p95. Partial results trade completeness for an answer
  inside the budget.
- I would propagate the request deadline from Kong's budget through the agent loop, give each tool a
  call budget checked in CI with trace assertions, run a peak-latency load test for every tool change,
  and alert on tool span p95.
