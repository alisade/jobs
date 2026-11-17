# Shopping assistant: requirements (from the product brief, v3)

Kestrel Outfitters wants one shopping assistant behind two front ends:

- **Web and mobile storefront:** a chat panel on product and search pages. Answers stream token by token.
- **Store associate app:** a tablet app used on the floor in all 140 stores. Associates ask "do we have
  the Ridgeline 2P in green at 087 or nearby?" and look up customer orders. Associates authenticate with
  store SSO and act within their store's scope.

## Capabilities (phase 1)

| Tool | Data owner | Read/write | Notes |
|---|---|---|---|
| `search_products` | Catalog team | read | full-text + filters, prices |
| `check_inventory` | Catalog team (inventory lives in catalog-db today) | read | stock per store, volatile |
| `get_order_status` | Orders team | read | customer must be signed in; associate only for own store |
| `start_return` | Orders team | write | user must confirm in the UI before it runs |

## Traffic and latency

| Metric | Normal | Holiday peak (Black Friday week) |
|---|---|---|
| Conversations per day | 18,000 | 220,000 (about 12x) |
| Peak concurrent streams | 300 | 3,600 |
| Model calls per conversation | 3.2 average (tool loop) | same |
| Target p95 time to first token | 1.5 s | 2.5 s acceptable |
| Target p95 full answer | 8 s | 12 s |

## Cost

- Budget: average 2.5 cents per conversation in model spend, hard ceiling 10 cents per conversation.
- Finance wants model spend per feature (storefront vs associate app) every week.

## Teams

- **Catalog team** (7 engineers): owns `catalog-service` and catalog-db (Postgres). Releases twice a week.
- **Orders team** (9 engineers): owns `order-service` and its database. PCI scope adjacent; very
  conservative release process, monthly change window in Q4.
- **AI team** (new, 4 engineers including you): owns the assistant. Python and TypeScript.
- **Platform team** (5 engineers): EKS, the API gateway (Kong), the CDN, observability (OpenTelemetry to
  a hosted backend). Runs the on-call for shared infrastructure.

## Non-functional

- The assistant must fail soft: if it is down, the storefront search box and the order pages still work.
- A product-search answer must never show a price or stock that the catalog did not return.
- All model calls must be traceable per conversation (tokens, cost, latency, model, prompt version).
