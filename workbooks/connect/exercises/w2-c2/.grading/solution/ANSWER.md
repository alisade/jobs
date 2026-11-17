# ANSWER: connect/w2-c2 Routing simulator: tune the LFG routing design

## Approach

Event loop over interesting seconds only (arrivals, completions, abandons, delay and step expiries),
phases in the README order; one test per rule with hand-built scenarios.

## Fix

Baseline: PR 100%, general 89%, apps 53% (20% abandon), VIP 46% (46% abandon). Apps team took general
at priority 1; VIP shared priority 1 with general; tier 1 idle. Tuned: dedicated queue first, shared
queues at priority 2-3 with delays (tier1 general +10 s, generalists PR +20 s and apps, apps general
+45 s, VIP apps then general +90 s). Result: PR 87%, general 82%, apps 95%, VIP 96%.

## Trade-offs / what I would do in production

Seeds 1-3 put general at 70-81%: add two general agents at peak or offer callbacks. The model ignores
ACW, statuses, chat concurrency and callbacks; validate with Connect historical metrics after go-live.
