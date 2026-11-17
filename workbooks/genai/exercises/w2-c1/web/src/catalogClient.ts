// Typed client for the Kestrel catalog API.
//
// TODO (README "TypeScript client"):
//   - build on the GENERATED types in ./catalog-api (run `make contract` after the service is done),
//     not on hand-written interfaces
//   - listProducts(params): omit undefined/null/empty params, URL-encode values
//   - getProduct(sku): encode the sku in the path
//   - reserve(body, idempotencyKey): POST JSON with the Idempotency-Key header
//   - non-2xx: throw CatalogError; parse application/problem+json into its fields, otherwise
//     type "about:blank", title = statusText, detail ""
import type { Product, ProductList } from "./catalog-api";

export type FetchLike = (url: string, init?: RequestInit) => Promise<Response>;

export interface Problem {
  type: string;
  title: string;
  status: number;
  detail: string;
}

export class CatalogError extends Error {
  readonly status: number;
  readonly type: string;
  readonly title: string;
  readonly detail: string;
  constructor(p: Problem) {
    super(`${p.status} ${p.title}: ${p.detail}`);
    this.name = "CatalogError";
    this.status = p.status;
    this.type = p.type;
    this.title = p.title;
    this.detail = p.detail;
  }
}

export function buildQuery(params: Record<string, string | number | boolean | null | undefined>): string {
  return "?" + Object.entries(params).map(([k, v]) => `${k}=${v}`).join("&");
}

export function createCatalogClient(baseUrl: string, fetchImpl: FetchLike) {
  return {
    async listProducts(params: Record<string, string | number | undefined> = {}): Promise<ProductList> {
      const res = await fetchImpl(baseUrl + "/products" + buildQuery(params));
      return (await res.json()) as ProductList;
    },
    async getProduct(sku: string): Promise<Product> {
      const res = await fetchImpl(baseUrl + "/products/" + sku);
      return (await res.json()) as Product;
    },
  };
}
