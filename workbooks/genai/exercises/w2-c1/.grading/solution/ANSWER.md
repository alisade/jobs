# ANSWER: genai/w2-c1 Catalog service and its typed TypeScript client

## Approach

I treated the Pydantic models as the source of truth: models, then OpenAPI, then the committed
contract, then generated TypeScript types, then the client. I wrote the service tests first, one per
contract row: a cursor walk across pages, problem shapes, replay and conflict for reservations. Then I
ran `make contract` and wrote the client against the generated types until `tsc` passed.

## Fix

- Keyset pagination on (price_cents, sku) with an opaque cursor; `limit + 1` detects the last page;
  limit capped at 50; bad cursor is a 400 problem.
- `ProblemError` + one exception handler emits RFC 9457 problems; every route declares its problem
  responses, so the TS types include them.
- Reservations store the Idempotency-Key with a request hash. A replay returns the stored response, a
  different body is a 422, short stock is a 409 with no write, and a race on the unique key is caught.
- Client: generated types only, cleaned and encoded query, encoded sku, Idempotency-Key header,
  `CatalogError` from problem+json with a fallback for non-JSON bodies.

## Trade-offs / what I would do in production

- Keyset paging cannot jump to page N. That is fine for search results and infinite scroll.
- On Postgres I would decrement with a conditional UPDATE, check the row count, and expire keys after
  48 h.
- CI on the service repo exports the contract and fails on drift. The front end regenerates from a
  pinned contract version, and breaking changes get a new path version.
