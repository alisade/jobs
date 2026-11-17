# PAGE: assistant latency and model spend up since 2026-11-10 (sev3)

**Opened:** 2026-11-12 10:05 PT by FinOps  **Service:** kestrel-assistant (prod)

> Provider invoice preview for 11/10-11/11 is 3.1x the previous two days at the same traffic.
> Our own cost dashboard shows spend roughly FLAT. Which number is right?
> Also: assistant p50 time to first token went from 0.9 s to 2.6 s on 11/10.

## Thread (#inc-assistant-cost)

**10:09 ai-team:** the provider console says our prompt cache hit rate dropped from 87% to about 2%
on 11/10. Nothing about caching changed in our release.

**10:12 ai-team:** release 2026.11.10 added the current date and time to every request so the
assistant can answer "is the store open now?". That changes every request, so the cache can never
hit. We should drop the timestamp.

**10:15 platform:** the pods restarted for the release, and HPA has been scaling between 9 and 14 pods
since. Each pod runs 4 gunicorn workers.

**10:18 finops:** if caching is broken, why does our dashboard not show it?

You own the assistant service. Find why the cache stopped hitting, fix it, and fix the dashboard.
