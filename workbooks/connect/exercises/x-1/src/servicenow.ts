// Minimal ServiceNow Table API client used by the help desk Lambdas.
// OAuth 2.0 client credentials (token cached until shortly before expiry), JSON in/out,
// per-request timeout, retries with backoff on 429 (Retry-After), 5xx and timeouts.
export interface ServiceNowConfig {
  baseUrl: string;
  clientId: string;
  clientSecret: string;
  /** per-attempt timeout */
  timeoutMs?: number;
  /** extra attempts after the first */
  maxRetries?: number;
  sleep?: (ms: number) => Promise<void>;
}

export class ServiceNowError extends Error {
  constructor(public status: number, message: string, public ambiguous = false) {
    super(message);
  }
}

export interface RequestOptions {
  /** set false to disable retries for this call */
  retry?: boolean;
}

export class ServiceNowClient {
  private token: { value: string; expiresAt: number } | null = null;
  readonly timeoutMs: number;
  readonly maxRetries: number;
  private sleep: (ms: number) => Promise<void>;

  constructor(private cfg: ServiceNowConfig) {
    this.timeoutMs = cfg.timeoutMs ?? 2500;
    this.maxRetries = cfg.maxRetries ?? 2;
    this.sleep = cfg.sleep ?? ((ms) => new Promise((r) => setTimeout(r, ms)));
  }

  private async accessToken(): Promise<string> {
    if (this.token && this.token.expiresAt > Date.now() + 60_000) return this.token.value;
    const res = await fetch(`${this.cfg.baseUrl}/oauth_token.do`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ grant_type: "client_credentials", client_id: this.cfg.clientId, client_secret: this.cfg.clientSecret }).toString(),
    });
    if (!res.ok) throw new ServiceNowError(res.status, `token request failed: ${res.status}`);
    const j = (await res.json()) as { access_token: string; expires_in: number };
    this.token = { value: j.access_token, expiresAt: Date.now() + j.expires_in * 1000 };
    return j.access_token;
  }

  /** One HTTP call with retries. Returns parsed JSON body. */
  async request<T = any>(method: string, path: string, body?: unknown, opts: RequestOptions = {}): Promise<T> {
    const attempts = opts.retry === false ? 1 : 1 + this.maxRetries;
    let last: ServiceNowError | null = null;
    for (let i = 0; i < attempts; i++) {
      if (i > 0) await this.sleep(last && last.status === 429 ? 0 : 100 * 2 ** i);
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), this.timeoutMs);
      try {
        const res = await fetch(`${this.cfg.baseUrl}${path}`, {
          method,
          headers: { Authorization: `Bearer ${await this.accessToken()}`, "Content-Type": "application/json", Accept: "application/json" },
          body: body === undefined ? undefined : JSON.stringify(body),
          signal: ctrl.signal,
        });
        if (res.status === 401) {
          this.token = null;
          last = new ServiceNowError(401, "unauthorized");
          continue;
        }
        if (res.status === 429) {
          const ra = Number(res.headers.get("Retry-After") || "1");
          last = new ServiceNowError(429, "rate limited");
          await this.sleep(Math.min(ra, 2) * 1000);
          continue;
        }
        if (res.status >= 500) {
          // 502/503/504: the request may or may not have been processed
          last = new ServiceNowError(res.status, `server error ${res.status}`, true);
          continue;
        }
        const text = await res.text();
        const json = text ? JSON.parse(text) : {};
        if (!res.ok) throw new ServiceNowError(res.status, (json.error && json.error.message) || `HTTP ${res.status}`);
        return json as T;
      } catch (err: any) {
        if (err instanceof ServiceNowError) throw err;
        // timeout or network error: the request may or may not have reached ServiceNow
        last = new ServiceNowError(0, `network/timeout: ${err && err.name}`, true);
      } finally {
        clearTimeout(timer);
      }
    }
    throw last ?? new ServiceNowError(0, "no attempts");
  }
}
