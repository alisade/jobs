# ANSWER: genai/w5-t1 Assistant answers time out at peak

## Approach

<!-- How you investigated: which trace first, what you counted, what make demo showed. -->

## Root cause

<!-- The mechanism, with evidence: span counts and durations from both traces, the release note,
catalog latency at peak, the assistant log line. Why short questions work, why only at peak, why
switching providers would or would not help. -->

## Fix

<!-- What you changed and how you verified it (make demo before/after, tests). -->

## Trade-offs / what I would do in production

<!-- Short. Batch vs bounded fan-out, deadline propagation across services, partial answers in the UX,
how to catch N+1 tool calls before release (trace assertions, call-count budgets, load tests). -->
