# ANSWER: genai/ai-t1 Prompt cache hit rate fell to zero after the release

## Approach

<!-- Which evidence first; how you compared the two request dumps; what make demo showed. -->

## Root cause

<!-- The mechanism with evidence: what differs in the prefix between workers and why; why some requests
still hit; why the timestamp is or is not the cause; why our dashboard stayed flat. -->

## Fix

<!-- What you changed and how you verified it (demo output, tests). -->

## Trade-offs / what I would do in production

<!-- Short. A prefix-hash metric per request, a CI test across hash seeds, alert on cache hit ratio,
reconcile the dashboard with the invoice, where dynamic context belongs. -->
