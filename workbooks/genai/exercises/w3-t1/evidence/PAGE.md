# Ticket FIN-2291: model provider spend anomaly (assistant)

**Opened:** 2026-11-12 07:40 PT by finance-ops  **Assigned:** you (assistant platform on call)

> The provider's spend alert fired overnight. Daily spend for the shopping assistant project went from
> about $410 (Nov 3-10 average) to $3,710 on Nov 11. At this rate the December budget is gone by Dec 9.
> Please explain what changed and stop it today. Usage export attached (`usage-export.csv`, a sample of
> 40 conversations from Nov 11 morning).

## Thread

**07:52 growth-marketing:** the holiday preview email went out Nov 11 at 06:00 to 1.2M subscribers.
Assistant sessions were up about 30 percent. That is probably it?

**08:05 assistant-pm:** we shipped the "compare products" prompt on Nov 10 (release 2026.11.10). Some
customers also say comparison questions show "Sorry, something went wrong" after a long wait.

**08:11 sre:** gateway p99 latency is 80 s on comparison questions. Error rate on `/assistant/answer`
went from 0.2 percent to 31 percent. Nothing is down at the provider, their status page is green.

Find the root cause, show it from the evidence, and fix the gateway so this cannot cost us like this
again. Finance also asks: can we tell from our own logs, next time, what a request really cost?
