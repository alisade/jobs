# PAGE: assistant-service answer error rate above 8 percent (sev2)

**Fired:** 2026-11-18 17:05 PT  **Service:** assistant-service (prod)  **On call:** you

> 504 rate on POST /api/assistant/stream 11.4 percent for 10 min (SLO 1 percent).
> Storefront chat panel shows "Something went wrong" after a long "typing" state.

## Thread (#inc-assistant)

**17:07 web-oncall:** shoppers wait about 30 s, then the panel errors. It started around 16:40 when
evening traffic picked up. Short questions ("what is your return policy") still work.

**17:10 ai-team (Priya):** traces show the model calls are our longest spans, 2.1-2.3 s each. Provider A
latency is up a bit at peak. Should we fail over to provider B? It is faster.

**17:12 platform-oncall:** Kong is returning 504 because the assistant upstream does not finish within
the route's 30 s timeout. Kong itself is healthy, CPU 20 percent.

**17:15 catalog-oncall:** catalog-service is busy (evening peak plus the holiday email) but within SLO:
p50 about 700 ms, no errors. We are not paging.

**17:18 ai-team (Priya):** we shipped 2026.11.18 this morning, but it only touched a tool, not the model
or prompts.

Find the root cause before anyone flips the provider.
