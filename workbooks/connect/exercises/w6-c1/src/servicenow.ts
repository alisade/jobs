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
  constructor(private opts: SnOptions) {}

  /**
   * TODO: create the QA task unless one with the same correlation_id exists (safe to call again).
   * OAuth client credentials against /oauth_token.do (cache the token; refresh early; on a 401
   * re-authenticate once), Table API on /api/now/table/<table>, Retry-After on 429, bounded
   * backoff on 5xx, at most maxAttempts per request, fail fast on 4xx. Use opts.sleep for waits.
   */
  async ensureTask(t: QaTaskInput): Promise<QaTaskResult> {
    throw new Error(`TODO: ensureTask ${t.correlationId} via ${this.opts.baseUrl}`);
  }
}
