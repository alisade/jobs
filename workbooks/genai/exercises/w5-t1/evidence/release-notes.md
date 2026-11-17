# assistant-service 2026.11.18 (deployed 2026-11-18 09:30 PT)

- check_inventory now covers every product in the answer, not only the first 3. Product managers want
  "in stock at your store" badges on all suggested items. Typical answers suggest 8-20 products; the
  tool checks the shopper's store and the nearest other store.
- search_products returns up to 20 products (was 10).
- No prompt or model changes. Prompt version still `shop-v14`.

Known: catalog-service has offered `POST /inventory/lookup` (up to 50 sku/store pairs per call, same
p50 as a single GET) since 2026.08. The assistant still uses the single GET.
