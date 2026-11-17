# Reference: genai/w2-c1

Files: `.grading/solution/catalog/app.py`, `.grading/solution/web/src/catalogClient.ts`, the generated
`catalog-api.ts` and `contracts/openapi.json`.

- **Pagination:** keyset on `(price_cents, sku)`: `WHERE price > p OR (price = p AND sku > s) ORDER BY
  price, sku LIMIT n + 1`. The cursor is base64 JSON of the last key, validated on decode (400
  problem). Offset paging skips or repeats items when rows change between requests, and its cost grows
  with the offset.
- **Problems:** a `ProblemError` exception and one handler return `application/problem+json`. Each route
  declares `responses={404: {"model": Problem, "content": {"application/problem+json": ...}}}` so the
  generated client types include the error shapes.
- **Idempotency:** store the key with a hash of the request body. A replay with the same hash returns
  the stored result, and a different hash is a 422. A unique constraint on the key catches the race
  where two retries arrive at the same moment. On Postgres, decrement with
  `UPDATE inventory SET reserved = reserved + :q WHERE sku = :s AND store_id = :st AND on_hand - reserved >= :q`
  and check the row count, or lock the row with `SELECT ... FOR UPDATE`. Expire keys after 24-72 h.
- **Contract flow:** Pydantic models produce OpenAPI (`app.openapi()`), which goes into the committed
  `contracts/openapi.json`, which openapi-typescript turns into `catalog-api.ts`, which the client
  consumes. CI fails when the export or the generated types differ from what is committed. The front end
  pins a contract version.
- **Client:** sorted, filtered `URLSearchParams`, `encodeURIComponent` on path segments, and a
  problem+json parse with a fallback for proxy error pages.
