# genai/w2-c1 - Catalog service and its typed TypeScript client

**Type:** coding (full stack: Python + TypeScript) | **Estimate:** 2.5-3 hours | **Study plan:** Week 2
(FastAPI beyond hello world, SQLAlchemy 2.0, pytest, OpenAPI to TypeScript types)

## Scenario

The shopping assistant and the new React storefront both need product search, product detail with stock
per store, and a way to hold an item for in-store pickup. The catalog team's hack-week prototype runs, but
it uses offset paging (items shift while a shopper pages), plain-text errors, no reservations, and the
React app uses hand-written TypeScript types that already disagree with the service (`price` vs
`price_cents`). You own the contract: the service, the OpenAPI document, and the typed client the front
end imports.

## What you have

| Path | What it is |
|---|---|
| `catalog/db.py` | SQLAlchemy 2.0 models (Product, Inventory, Reservation) and seed data: 40 products, stores 012/045/087 (complete) |
| `catalog/schemas.py` | Pydantic contract models, including `Problem` (complete) |
| `catalog/app.py` | the prototype service with TODOs |
| `catalog/export_openapi.py` | prints `app.openapi()` |
| `contracts/openapi.json` | the exported contract (stale: from the prototype) |
| `web/src/catalog-api.ts` | hand-written types (stale); `make contract` replaces it with generated types |
| `web/src/catalogClient.ts` | the TypeScript client with TODOs |
| `tests/` | visible pytest and jest tests |

## Contract (what to build)

All error responses are RFC 9457 problem details (`Problem`) with media type `application/problem+json`
and a `type` URI under `https://api.kestrel.example/problems/`. Declare them in the OpenAPI responses so
the client gets the type.

| Operation | operation_id | Behaviour |
|---|---|---|
| `GET /healthz` | `health` | `{"status": "ok"}` |
| `GET /products` | `listProducts` | `ProductPage`. `q` matches name or description, case-insensitive. `category`, `max_price_cents`, and `in_stock_at=<store>` filter (available = on_hand - reserved > 0 at that store). Order is `price_cents`, then `sku`. `limit` defaults to 20 and is capped at 50 (51 is a 422). `next_cursor` is an opaque cursor (keyset on price and sku, not an offset), null on the last page. An invalid cursor is a 400 problem. |
| `GET /products/{sku}` | `getProduct` | `ProductDetail`, stock per store sorted by store id, `available` = on_hand - reserved; unknown sku is a 404 problem |
| `POST /inventory/reservations` | `createReservation` | body `ReservationRequest`, required header `Idempotency-Key`; 201 `ReservationCreated` (`reservation_id` like `r-000001`). The same key with the same body returns the same response and reserves nothing more. The same key with a different body is a 422 problem. Not enough stock is a 409 problem that changes nothing. A sku/store with no inventory row is a 404 problem. |

## TypeScript client

1. `make contract` exports `contracts/openapi.json` and generates `web/src/catalog-api.ts` with
   openapi-typescript. Commit both. Never edit the generated file by hand.
2. Rewrite `web/src/catalogClient.ts` on the generated types (`components["schemas"][...]`,
   `operations["listProducts"]["parameters"]["query"]`). It must:
   - drop undefined, null and empty params and URL-encode the rest;
   - encode the sku in the path;
   - POST reservations as JSON with the `Idempotency-Key` header;
   - throw `CatalogError` for non-2xx. Parse a problem+json body into its fields; for any other
     body use type `about:blank`, title = `statusText` and detail `""`.
3. `tsc --noEmit -p web/tsconfig.json` must pass.

## Acceptance criteria (what the grader checks)

- Search, filters, cursor walk (every item exactly once, in order), the page cap, problem responses.
- Idempotent reservations, no overselling across different keys, 409 changes nothing.
- The operation ids are exactly the four above. `contracts/openapi.json` equals `app.openapi()`.
- `catalog-api.ts` is exactly what openapi-typescript generates from the committed contract, and the
  client type-checks against it.
- The client behaviour in "TypeScript client" above.

## How to run

```bash
make setup      # shared venv + node toolchain
make test       # visible pytest + jest
make contract   # export OpenAPI, regenerate TS types, type-check web/
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade genai/w2-c1
make clean
```
