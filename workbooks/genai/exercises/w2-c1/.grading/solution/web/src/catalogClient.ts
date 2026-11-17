// Typed client for the Kestrel catalog API, built on the generated types. Reference solution.
import type { components, operations } from "./catalog-api";

export type ProductSummary = components["schemas"]["ProductSummary"];
export type ProductPage = components["schemas"]["ProductPage"];
export type ProductDetail = components["schemas"]["ProductDetail"];
export type ReservationRequest = components["schemas"]["ReservationRequest"];
export type ReservationCreated = components["schemas"]["ReservationCreated"];
export type Problem = components["schemas"]["Problem"];
export type ListProductsParams = NonNullable<operations["listProducts"]["parameters"]["query"]>;

export type FetchLike = (url: string, init?: RequestInit) => Promise<Response>;

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
  const sp = new URLSearchParams();
  for (const key of Object.keys(params).sort()) {
    const v = params[key];
    if (v === undefined || v === null || v === "") continue;
    sp.append(key, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

async function toError(res: Response): Promise<CatalogError> {
  const type = res.headers.get("content-type") || "";
  if (type.includes("application/problem+json")) {
    try {
      return new CatalogError((await res.json()) as Problem);
    } catch {
      /* fall through */
    }
  }
  return new CatalogError({ type: "about:blank", title: res.statusText || "HTTP error", status: res.status, detail: "" });
}

export function createCatalogClient(baseUrl: string, fetchImpl: FetchLike) {
  const base = baseUrl.replace(/\/+$/, "");
  async function call<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetchImpl(base + path, { ...init, headers: { Accept: "application/json", ...(init?.headers || {}) } });
    if (!res.ok) throw await toError(res);
    return (await res.json()) as T;
  }
  return {
    listProducts(params: ListProductsParams = {}): Promise<ProductPage> {
      return call<ProductPage>("/products" + buildQuery(params));
    },
    getProduct(sku: string): Promise<ProductDetail> {
      return call<ProductDetail>("/products/" + encodeURIComponent(sku));
    },
    reserve(body: ReservationRequest, idempotencyKey: string): Promise<ReservationCreated> {
      return call<ReservationCreated>("/inventory/reservations", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
        body: JSON.stringify(body),
      });
    },
  };
}
