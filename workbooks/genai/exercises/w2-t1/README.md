# genai/w2-t1 - Catalog search p95 went from 80 ms to 4 s and pods fail health checks

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 2 (FastAPI concurrency and
async/await, dependency injection, testing with dependency overrides)

## Symptom

Kestrel Outfitters' `catalog-search` service breached its latency SLO the morning after a release. Search
on the storefront and the assistant's `search_products` tool both stall, pods restart on liveness
failures, and scaling out did not help. Read `evidence/PAGE.md` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/PAGE.md` | the page and the incident thread |
| `evidence/release-notes.md` | what shipped, and how the service is deployed |
| `evidence/latency-by-endpoint.txt` | latency percentiles per route, before and after |
| `evidence/kubelet-events.txt` | probe failures and restarts |
| `evidence/py-spy-dump.txt` | a stack dump from a struggling pod |
| `evidence/slow-query.log` | the database slow-query entry the DBA found |
| `catalog_search/app.py` | the service (FastAPI) |
| `catalog_search/promotions_sdk.py` | the vendor SDK, vendored as shipped: do not edit it |
| `scripts/demo.py` | `make demo` reproduces the incident in-process: concurrent searches plus health probes |

## Your task

1. Find the root cause and prove it with the evidence: quote the lines that show it, explain why the
   health checks fail, why the HPA scale-out did not help, and whether the slow query matters.
2. Fix `catalog_search/app.py` (not the SDK) so that:
   - one slow search can never stall other requests or `/healthz` on the same worker;
   - the promotions call is bounded (at most about 300 ms) and search degrades instead of failing: a slow
     or failing PromoHub returns the results without badges and `"promotions_degraded": true` (and
     `false` when badges were applied);
   - a search with no results does not call PromoHub;
   - search results, filters and limits behave as before.
3. Verify with `make demo` (health probes should stay in milliseconds) and `make test`.
4. Write `ANSWER.md`: Approach, Root cause (with evidence), Fix (and verification), Trade-offs / what you
   would do to stop this class of bug.

## Acceptance criteria (what the grader checks)

- `/healthz` answers in well under 200 ms while 8 slow searches are in flight on one event loop.
- 8 concurrent searches overlap instead of running one after another.
- A 1.5 s PromoHub answer is cut off, the response comes back in under 0.8 s with
  `promotions_degraded: true`; a PromoHub error gives 200 with degraded results.
- No PromoHub call for an empty result; existing search behaviour unchanged.
- `ANSWER.md` names the mechanism precisely, with evidence, and rules out the red herring.

## How to run

```bash
make setup     # shared Python venv (first run builds genai/.venv)
make demo      # reproduce: search latency and health probe latency
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade genai/w2-t1
make clean
```
