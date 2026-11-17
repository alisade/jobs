# ANSWER: genai/w3-t1 The assistant's model bill went up 9x overnight

## Approach

<!-- Which evidence first, what make report and make demo showed, what you ruled out. -->

## Root cause

<!-- The mechanism, with evidence: usage-export rows (same fingerprint billed N times, durations),
gateway log lines, the traffic table. The multiplier per question and why comparisons fail. -->

## Fix

<!-- What you changed in gateway.py and how you verified it (tests, make demo before/after). -->

## Trade-offs / what I would do in production

<!-- Short. Streaming vs long timeouts, retry budgets across layers, where cost caps live,
alerts on billed-vs-delivered tokens, what finance should see per request. -->
