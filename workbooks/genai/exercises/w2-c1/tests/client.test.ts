import { createCatalogClient } from "../web/src/catalogClient";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

test("listProducts calls GET /products on the base URL", async () => {
  const fetchImpl = jest.fn(async () => jsonResponse({ items: [], next_cursor: null }));
  const c = createCatalogClient("https://api.kestrel.example", fetchImpl);
  await c.listProducts({});
  const url = String((fetchImpl.mock.calls[0] as unknown[])[0]);
  expect(url.startsWith("https://api.kestrel.example/products")).toBe(true);
});
