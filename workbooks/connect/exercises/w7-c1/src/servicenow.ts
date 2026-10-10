// ServiceNow Table API client for a Lambda invoked synchronously from an Amazon Connect flow.
// The contractor's first cut: it works on a quiet afternoon in the dev instance. See README.md.

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

export class ServiceNowClient {
  private readonly pageSize: number;
  private readonly clock: Clock;
  private readonly fetchImpl: typeof fetch;

  constructor(private readonly cfg: ServiceNowConfig) {
    this.pageSize = cfg.pageSize ?? 50;
    this.clock = cfg.clock ?? realClock;
    this.fetchImpl = cfg.fetchImpl ?? fetch;
  }

  // TODO: cache the token (Lambda containers are reused) and refresh it before it expires.
  async accessToken(_deadline: number, _force = false): Promise<string> {
    const res = await this.fetchImpl(`${this.cfg.baseUrl}/oauth_token.do`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" },
      body: new URLSearchParams({ grant_type: "client_credentials", client_id: this.cfg.clientId, client_secret: this.cfg.clientSecret }).toString(),
    });
    if (!res.ok) throw new ServiceNowError(`token endpoint returned ${res.status}`, res.status);
    const body = (await res.json()) as { access_token: string; expires_in: number };
    return body.access_token;
  }

  // TODO: 401 -> refresh the token once and retry; 429 -> honor Retry-After but never past the deadline.
  async call(method: string, path: string, deadline: number, body?: unknown): Promise<Response> {
    const token = await this.accessToken(deadline);
    const res = await this.fetchImpl(`${this.cfg.baseUrl}${path}`, {
      method,
      headers: { Authorization: `Bearer ${token}`, Accept: "application/json", ...(body ? { "Content-Type": "application/json" } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) throw new ServiceNowError(`${method} ${path.split("?")[0]} returned ${res.status}`, res.status);
    return res;
  }

  // TODO: follow pagination (Link rel="next") so callers see every record.
  async listAll<T>(table: string, query: string, fields: string[], deadline: number): Promise<T[]> {
    const qs = new URLSearchParams({ sysparm_query: query, sysparm_fields: fields.join(","), sysparm_limit: String(this.pageSize) });
    const res = await this.call("GET", `/api/now/table/${table}?${qs.toString()}`, deadline);
    const body = (await res.json()) as { result: T[] };
    return body.result;
  }

  async create<T>(table: string, record: Record<string, string>, deadline: number): Promise<T> {
    const res = await this.call("POST", `/api/now/table/${table}`, deadline, record);
    return ((await res.json()) as { result: T }).result;
  }
}

/** Parse an RFC 8288 Link header and return the path+query of rel="next", or null. */
export function nextLink(_link: string | null): string | null {
  return null; // TODO
}
