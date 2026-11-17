# Current architecture (as of 2026-11)

```text
 browser / mobile app                 store tablets (associate app, React Native)
        |                                      |
        v                                      v
   CDN (caches static + some GET APIs, 60 s origin read timeout, response buffering ON by default)
        |
        v
   Kong API gateway on EKS (auth plugin: storefront JWT / store SSO; rate limits per consumer;
                            upstream timeout 30 s; HTTP/1.1 to upstreams)
        |
   +----+---------------------+------------------------+
   |                          |                        |
 storefront (monolith,     catalog-service          order-service
 Node/Express, SSR,        (Python FastAPI)         (Java, Spring Boot)
 owned by Web team)        catalog-db Postgres      orders-db Postgres
                           (products, prices,       (orders, returns,
                            inventory)               payments refs)
```

Notes:

- The storefront monolith renders pages and calls catalog-service and order-service over HTTP through
  internal service DNS (not through Kong).
- catalog-service has a read replica; several batch jobs read catalog-db directly (this is a known
  pain point: a schema change broke two of them last spring).
- Kong supports HTTP streaming responses if `response_buffering` is off for the route; nobody has done
  it yet. WebSocket is supported by Kong but the CDN in front only supports WebSocket on a separate,
  more expensive tier that is not enabled.
- There is no LLM usage in production today. Two internal hack-week prototypes called a model API
  directly from laptops.
- Egress to the internet from EKS goes through an egress proxy with an allow list (see constraints.md).
