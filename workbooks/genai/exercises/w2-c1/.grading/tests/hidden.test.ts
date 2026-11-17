import { execFileSync } from "child_process";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { buildQuery, CatalogError, createCatalogClient } from "../../web/src/catalogClient";

const ROOT = process.cwd();
const BIN = (n: string) => path.join(ROOT, "node_modules", ".bin", n);

function res(body: unknown, status = 200, type = "application/json", statusText = ""): Response {
  return new Response(typeof body === "string" ? body : JSON.stringify(body), { status, statusText, headers: { "content-type": type } });
}
const calls = (f: jest.Mock) => f.mock.calls as unknown as [string, RequestInit | undefined][];

test("query string omits empty params and encodes values", () => {
  const q = buildQuery({ q: "rain & wind", category: undefined, max_price_cents: 5000, cursor: null, in_stock_at: "" });
  const sp = new URLSearchParams(q.replace(/^\?/, ""));
  expect(sp.get("q")).toBe("rain & wind");
  expect(sp.get("max_price_cents")).toBe("5000");
  expect(sp.has("category")).toBe(false);
  expect(sp.has("cursor")).toBe(false);
  expect(sp.has("in_stock_at")).toBe(false);
  expect(q).not.toContain(" ");
  expect(buildQuery({})).toBe("");
});

test("listProducts returns the page and passes the cursor", async () => {
  const f = jest.fn(async () => res({ items: [{ sku: "KO-LAMP-1", name: "Trail Lantern", category: "lighting", price_cents: 3450 }], next_cursor: "abc" }));
  const c = createCatalogClient("https://api.kestrel.example/", f);
  const page = await c.listProducts({ q: "lantern", cursor: "WzM0NTAsIktPIl0=" });
  expect(page.next_cursor).toBe("abc");
  expect(page.items[0].price_cents).toBe(3450);
  const url = new URL(calls(f)[0][0]);
  expect(url.pathname).toBe("/products");
  expect(url.searchParams.get("cursor")).toBe("WzM0NTAsIktPIl0=");
});

test("getProduct encodes the sku in the path", async () => {
  const f = jest.fn(async () => res({}));
  await createCatalogClient("https://x", f).getProduct("KO/../admin");
  expect(calls(f)[0][0]).toBe("https://x/products/KO%2F..%2Fadmin");
});

test("problem+json errors become CatalogError with the problem fields", async () => {
  const problem = { type: "https://api.kestrel.example/problems/not-found", title: "Product not found", status: 404, detail: "no product with sku X" };
  const f = jest.fn(async () => res(problem, 404, "application/problem+json"));
  const err = await createCatalogClient("https://x", f).getProduct("X").catch((e) => e);
  expect(err).toBeInstanceOf(CatalogError);
  expect(err).toMatchObject(problem);
});

test("a non-problem error body still becomes a CatalogError", async () => {
  const f = jest.fn(async () => res("<html>gateway</html>", 502, "text/html", "Bad Gateway"));
  const err = await createCatalogClient("https://x", f).listProducts({}).catch((e) => e);
  expect(err).toBeInstanceOf(CatalogError);
  expect(err).toMatchObject({ status: 502, type: "about:blank", title: "Bad Gateway" });
});

test("reserve POSTs JSON with the Idempotency-Key header", async () => {
  const f = jest.fn(async () => res({ reservation_id: "r-000001", sku: "KO-LAMP-1", store_id: "045", quantity: 1, available_after: 3 }, 201));
  const c = createCatalogClient("https://x", f);
  const out = await c.reserve({ sku: "KO-LAMP-1", store_id: "045", quantity: 1 }, "chk-1-abcdefgh");
  expect(out.reservation_id).toBe("r-000001");
  const [url, init] = calls(f)[0];
  expect(url).toBe("https://x/inventory/reservations");
  expect(init?.method).toBe("POST");
  const h = new Headers(init?.headers);
  expect(h.get("Idempotency-Key")).toBe("chk-1-abcdefgh");
  expect(h.get("Content-Type")).toBe("application/json");
  expect(JSON.parse(String(init?.body))).toEqual({ sku: "KO-LAMP-1", store_id: "045", quantity: 1 });
});

test("web/src/catalog-api.ts is generated from contracts/openapi.json", () => {
  const out = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "oat-")), "api.ts");
  execFileSync(BIN("openapi-typescript"), [path.join(ROOT, "contracts", "openapi.json"), "-o", out], { stdio: "pipe", timeout: 60000 });
  expect(fs.readFileSync(path.join(ROOT, "web", "src", "catalog-api.ts"), "utf8")).toBe(fs.readFileSync(out, "utf8"));
});

test("the client type-checks against the generated types (tsc --noEmit)", () => {
  let output = "";
  try {
    execFileSync(BIN("tsc"), ["--noEmit", "-p", path.join(ROOT, "web", "tsconfig.json")], { stdio: "pipe", timeout: 90000 });
  } catch (e) {
    output = String((e as { stdout?: Buffer }).stdout || e);
  }
  expect(output).toBe("");
});
