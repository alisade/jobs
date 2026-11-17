# Reference: genai/w5-t1

## Root cause
Release 2026.11.18 changed `check_inventory` from the first 3 products to all products in the answer
(up to 20) for two stores. The tool loops over every (sku, store) pair and awaits one GET per pair:
40 sequential round trips, each with a 2 s timeout and no budget for the whole tool. Off peak, catalog
p50 is 0.18 s, so 40 calls take about 7.5 s and the answer still lands in about 12 s. At the evening
peak catalog p50 is 0.7 s (normal for its load and within its SLO), so the tool needs about 28 s.
Add two model calls of about 2.2 s each and the request passes Kong's 30 s route timeout. Short
questions call no or few products, so they still work.

## Evidence
- `trace-slow-request.json`: about 35 `GET /inventory/{sku}` spans under `execute_tool check_inventory`,
  each starting about 3 ms after the previous one ends (sequential), 0.6-1.2 s each. The tool span runs
  until the 30 s cut and the root span ends with status 504.
- `trace-normal-request.json`: 6 catalog spans (3 SKUs x 2 stores), about 1.1 s of tool time. The
  model span (2.3 s) is the longest single span. This is the red herring.
- `catalog-latency.txt`: calls per turn went from 6 to an average of 31 (max 40), and p50 at 17:00 was
  0.71 s against 0.16 s in the morning.
- `gateway-timeouts.log`: `phase=tool check_inventory ... completed_lookups=35/40`.

## Fix
The solution uses `batch_stock` in chunks of 50, a semaphore of 4, one deadline computed from
`deadline_s`, and a per-call timeout of min(0.8 s, remaining). When the deadline passes or a batch
fails it returns partial results flagged `stock_unknown`. `make demo` then shows about 5 s per answer
at peak, with one batch call.

## Prevention
- Propagate a deadline from the gateway budget into the agent loop and every tool.
- Set call-count and latency budgets per tool, checked in tests and visible in traces.
- Load test tools at peak dependency latency, not at the morning p50.
- Show "check stock on the product page" in the UI for unknown stock.
