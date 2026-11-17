# ANSWER: genai/w2-t1 Catalog search p95 went from 80 ms to 4 s

## Approach

<!-- How you investigated: which evidence first, what you reproduced with make demo, what you ruled out. -->

## Root cause

<!-- The mechanism, with evidence: quote the stack dump, the probe events, the latency table.
Why /healthz fails, why more pods did not help, why the slow query is or is not involved. -->

## Fix

<!-- What you changed in app.py and how you verified it (make demo output before/after, tests). -->

## Trade-offs / what I would do in production

<!-- Short. Threadpool vs async client vs cache for badges, timeouts and degradation, how to catch
blocking calls in async code before production (tests, lint, loop-lag metrics), probe design. -->
