/**
 * Minimal ServiceNow Table API client for QA tasks: OAuth 2.0 client credentials, token
 * caching with early refresh, one re-auth on 401, Retry-After on 429, bounded retries on
 * 5xx, and idempotent creation keyed by correlation_id.
 */
export interface QaTaskInput {
  correlationId: string; // `${contactId}:${ruleId}`
  shortDescription: string;
  description: string;
  priority: number; // 1-4
  assignmentGroup: string;
}
export interface QaTaskResult { sysId: string; number: string; created: boolean }

export interface SnOptions {
  baseUrl: string;
  clientId: string;
  clientSecret: string;
  table?: string; // default "task"
  maxAttempts?: number; // per request, default 4
  sleep?: (ms: number) => Promise<void>;
  now?: () => number;
}

export class ServiceNowError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

export class QaTaskClient {
  private token: { value: string; expiresAt: number } | null = null;
  private readonly table: string;
  private readonly maxAttempts: number;
  private readonly sleep: (ms: number) => Promise<void>;
  private readonly now: () => number;

  constructor(private opts: SnOptions) {
    this.table = opts.table || "task";
    this.maxAttempts = opts.maxAttempts || 4;
    this.sleep = opts.sleep || ((ms) => new Promise((r) => setTimeout(r, ms)));
    this.now = opts.now || Date.now;
  }

  private async getToken(force = false): Promise<string> {
    if (!force && this.token && this.token.expiresAt - 60_000 > this.now()) return this.token.value;
    const body = new URLSearchParams({ grant_type: "client_credentials", client_id: this.opts.clientId, client_secret: this.opts.clientSecret });
    const res = await fetch(`${this.opts.baseUrl}/oauth_token.do`, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body });
    if (!res.ok) throw new ServiceNowError(`token request failed: ${res.status}`, res.status);
    const j = (await res.json()) as { access_token: string; expires_in: number };
    this.token = { value: j.access_token, expiresAt: this.now() + j.expires_in * 1000 };
    return this.token.value;
  }

  private async request(method: string, path: string, body?: unknown): Promise<any> {
    let reauthed = false;
    for (let attempt = 1; ; attempt++) {
      const token = await this.getToken();
      const res = await fetch(`${this.opts.baseUrl}${path}`, {
        method,
        headers: { Authorization: `Bearer ${token}`, Accept: "application/json", "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      if (res.status === 401 && !reauthed) {
        reauthed = true;
        this.token = null;
        attempt--;
        continue;
      }
      if ((res.status === 429 || res.status >= 500) && attempt < this.maxAttempts) {
        const ra = Number(res.headers.get("retry-after"));
        const wait = res.status === 429 && Number.isFinite(ra) ? Math.min(ra * 1000, 10_000) : Math.min(200 * 2 ** (attempt - 1), 2_000);
        await this.sleep(wait);
        continue;
      }
      if (!res.ok) throw new ServiceNowError(`${method} ${path} -> ${res.status}`, res.status);
      return res.json();
    }
  }

  async findByCorrelation(correlationId: string): Promise<{ sys_id: string; number: string } | null> {
    const q = encodeURIComponent(`correlation_id=${correlationId}`);
    const j = await this.request("GET", `/api/now/table/${this.table}?sysparm_query=${q}&sysparm_limit=1&sysparm_fields=sys_id,number`);
    return j.result[0] || null;
  }

  /** Create the QA task unless one with the same correlation id exists (safe to call again on retry). */
  async ensureTask(t: QaTaskInput): Promise<QaTaskResult> {
    const existing = await this.findByCorrelation(t.correlationId);
    if (existing) return { sysId: existing.sys_id, number: existing.number, created: false };
    const j = await this.request("POST", `/api/now/table/${this.table}`, {
      correlation_id: t.correlationId,
      short_description: t.shortDescription,
      description: t.description,
      priority: String(t.priority),
      assignment_group: t.assignmentGroup,
    });
    return { sysId: j.result.sys_id, number: j.result.number, created: true };
  }
}
