# genai/w5-t1 - Assistant answers time out at peak while the model looks slow

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 5 (tracing, resilience
patterns, deadlines and timeouts across services); Week 3 (tool calls inside the agent loop)

## Symptom

At the evening peak, more than one in ten Kestrel Outfitters shopping-assistant answers ends in a
gateway timeout after about 30 seconds. Short questions still work. The AI team wants to fail over to
the second model provider because the model spans are the longest in the trace. Read `evidence/PAGE.md`
first.

## What you have

| Path | What it is |
|---|---|
| `evidence/PAGE.md` | the page and the incident thread |
| `evidence/release-notes.md` | what shipped this morning |
| `evidence/trace-normal-request.json` | OpenTelemetry-style spans for a normal request |
| `evidence/trace-slow-request.json` | spans for a request that hit the gateway timeout |
| `evidence/catalog-latency.txt` | catalog-service latency and call counts |
| `evidence/gateway-timeouts.log` | Kong errors and the matching assistant log line |
| `assistant_tools/inventory_tool.py` | the `check_inventory` tool (this is where the fix goes) |
| `assistant_tools/catalog_client.py` | catalog client interface and the local fake; do not edit |
| `scripts/demo.py` | `make demo`: one 20-product answer at normal and peak catalog latency |

## Your task

1. Find the root cause and prove it from the traces and logs. Quote span counts and durations. Explain
   why short questions still work, why it only fails at peak, and whether switching providers would help.
2. Fix `check_inventory` so that:
   - it uses the batch endpoint (`batch_stock`, at most 50 pairs per call) instead of one call per pair;
   - no more than 4 catalog calls are in flight at once;
   - it never spends more than `deadline_s` (the request's remaining budget; default 3 s), and no single
     call's timeout exceeds the remaining budget;
   - when the deadline hits or a batch fails, it returns the items it has, marks the rest
     `"stock_unknown": true` with `"available": null`, sets `"partial": true`, and does not raise;
   - results keep input order, duplicates are removed, and empty input makes no calls.
3. Verify with `make demo` and `make test`.
4. Write `ANSWER.md`: Approach, Root cause (with evidence), Fix (and verification), Trade-offs / what you
   would do to stop this class of bug.

## Acceptance criteria (what the grader checks)

- 20 products x 2 stores at 50 ms catalog latency complete in well under 0.4 s with one batch call.
- 300 pairs are split into batches of at most 50 with at most 4 in flight.
- With a 0.2 s budget and a 1.5 s catalog, the tool returns within about 0.45 s with all stock unknown.
- A failing batch only marks its own items unknown.
- `ANSWER.md` names the mechanism with evidence from the traces and rules out the red herring.

## How to run

```bash
make setup     # shared Python venv
make demo      # reproduce (time scaled 1:10)
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade genai/w5-t1
make clean
```
