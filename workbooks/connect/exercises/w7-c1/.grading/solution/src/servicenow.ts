// ServiceNow Table API client for a Lambda invoked synchronously from an Amazon Connect flow.
// Everything runs against one deadline: Connect gives a synchronous invoke at most 8 s, so the
// client never sleeps past the caller's budget and never retries past it.

export type Clock = { now(): number; sleep(ms: number): Promise<void> };
export const realClock: Clock = { now: () => Date.now(), sleep: (ms) => new Promise((r) => setTimeout(r, ms)) };

export class BudgetExceeded extends Error {}
export class ServiceNowError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

export type ServiceNowConfig = {
  baseUrl: string;
  clientId: string;
  clientSecret: string;
  pageSize?: number;
  maxRetries?: number;
  clock?: Clock;
  fetchImpl?: typeof fetch;
};

type Token = { value: string; expiresAt: number };

export class ServiceNowClient {
  private token: Token | null = null;
  private readonly pageSize: number;
  private readonly maxRetries: number;
  private readonly clock: Clock;
  private readonly fetchImpl: typeof fetch;

  constructor(private readonly cfg: ServiceNowConfig) {
    this.pageSize = cfg.pageSize ?? 50;
    this.maxRetries = cfg.maxRetries ?? 3;
    this.clock = cfg.clock ?? realClock;
    this.fetchImpl = cfg.fetchImpl ?? fetch;
  }

  /** OAuth 2.0 client credentials; cached until 60 s before expiry (Lambda container reuse). */
  async accessToken(deadline: number, force = false): Promise<string> {
    if (!force && this.token && this.token.expiresAt - 60_000 > this.clock.now()) return this.token.value;
    this.checkBudget(deadline);
    const res = await this.fetchImpl(`${this.cfg.baseUrl}/oauth_token.do`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" },
      body: new URLSearchParams({ grant_type: "client_credentials", client_id: this.cfg.clientId, client_secret: this.cfg.clientSecret }).toString(),
    });
    if (!res.ok) throw new ServiceNowError(`token endpoint returned ${res.status}`, res.status);
    const body = (await res.json()) as { access_token: string; expires_in: number };
    this.token = { value: body.access_token, expiresAt: this.clock.now() + Number(body.expires_in) * 1000 };
    return this.token.value;
  }

  private checkBudget(deadline: number) {
    if (this.clock.now() >= deadline) throw new BudgetExceeded("ServiceNow budget exhausted");
  }

  /** One Table API call with token refresh on 401 (once) and Retry-After on 429 (bounded by budget). */
  async call(method: string, path: string, deadline: number, body?: unknown): Promise<Response> {
    let refreshed = false;
    for (let attempt = 0; ; attempt++) {
      this.checkBudget(deadline);
      const token = await this.accessToken(deadline);
      const res = await this.fetchImpl(`${this.cfg.baseUrl}${path}`, {
        method,
        headers: { Authorization: `Bearer ${token}`, Accept: "application/json", ...(body ? { "Content-Type": "application/json" } : {}) },
        body: body ? JSON.stringify(body) : undefined,
      });
      if (res.status === 401 && !refreshed) {
        refreshed = true;
        this.token = null;
        continue;
      }
      if (res.status === 429 && attempt < this.maxRetries) {
        const secs = Number(res.headers.get("Retry-After") || "1");
        const waitMs = Math.max(0, (Number.isFinite(secs) ? secs : 1) * 1000);
        if (this.clock.now() + waitMs >= deadline) throw new BudgetExceeded(`Retry-After ${secs}s does not fit the remaining budget`);
        await this.clock.sleep(waitMs);
        continue;
      }
      if (!res.ok) throw new ServiceNowError(`${method} ${path.split("?")[0]} returned ${res.status}`, res.status);
      return res;
    }
  }

  /** List every matching record, following the Link rel="next" header page by page. */
  async listAll<T>(table: string, query: string, fields: string[], deadline: number): Promise<T[]> {
    const qs = new URLSearchParams({ sysparm_query: query, sysparm_fields: fields.join(","), sysparm_limit: String(this.pageSize), sysparm_offset: "0" });
    let path: string | null = `/api/now/table/${table}?${qs.toString()}`;
    const out: T[] = [];
    let pages = 0;
    while (path && pages++ < 100) {
      const res = await this.call("GET", path, deadline);
      const body = (await res.json()) as { result: T[] };
      out.push(...body.result);
      path = nextLink(res.headers.get("Link"));
    }
    return out;
  }

  async create<T>(table: string, record: Record<string, string>, deadline: number): Promise<T> {
    const res = await this.call("POST", `/api/now/table/${table}`, deadline, record);
    return ((await res.json()) as { result: T }).result;
  }
}

export function nextLink(link: string | null): string | null {
  if (!link) return null;
  for (const part of link.split(",")) {
    const m = /<([^>]+)>\s*;\s*rel="?next"?/.exec(part.trim());
    if (m) {
      const u = m[1];
      return u.startsWith("http") ? new URL(u).pathname + new URL(u).search : u;
    }
  }
  return null;
}

/** Encoded-query values must not inject extra clauses (^ splits clauses, , splits IN lists). */
export function q(value: string): string {
  return value.replace(/[\^,=]/g, "");
}
