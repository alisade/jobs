# PAGE: catalog-search p95 latency SLO burn (sev2)

**Fired:** 2026-11-05 09:12 PT  **Service:** catalog-search (prod, us-west-2)  **On call:** you

> catalog-search p95 latency 4.1 s (SLO 300 ms) for 15 min. Error budget burn rate 38x.
> Storefront search and the shopping assistant's search_products tool both affected.

## Thread (#inc-catalog-search)

**09:14 storefront-oncall:** search page spinners everywhere. Assistant answers are timing out too.

**09:16 platform-oncall:** catalog-search pods are restarting. `kubectl get pods` shows RESTARTS climbing
on all 6 replicas, liveness probe failures. HPA scaled from 6 to 12 and it did not help at all.
Node CPU is low (pods at about 9 percent of their CPU request).

**09:19 dba-oncall:** I see a slow-query log entry for the product search query, a sequential scan on
`products`. Maybe we need the trigram index we talked about? I can add it in about an hour.

**09:22 catalog-lead:** we shipped 2026.11.04 last night: promotion badges on search results through the
PromoHub SDK. PromoHub's status page is green and their p50 is 240 ms like always.

**09:24 storefront-oncall:** marketing's holiday email went out at 09:00, so traffic is up about 1.5x.

Find the root cause. Rolling back loses the badges marketing paid for, so they want a fix, not a revert,
if a safe one exists today.
