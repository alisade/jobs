// Rollout rules for the storefront assistant: flags, cohorts and the analytics schema.

export type Mode = "off" | "shadow" | "on";

export interface FlagValues {
  /** true = everyone gets legacy search, immediately */
  killSwitch: boolean;
  /** what users inside the rollout percentage get */
  mode: Mode;
  /** 0-100: share of users (by stable bucket) inside the rollout */
  percent: number;
}

export interface FlagClient {
  get(): FlagValues;
  /** called on every flag change; returns an unsubscribe function */
  subscribe(fn: (v: FlagValues) => void): () => void;
}

export type EventName =
  | "assistant_query"
  | "assistant_shadow_result"
  | "assistant_fallback"
  | "assistant_handoff";

export interface AnalyticsEvent {
  name: EventName;
  mode: Mode;
  bucket: number;
  queryHash: string;
  queryLength: number;
  outcome?: "done" | "error" | "timeout";
  ttftMs?: number | null;
  answerChars?: number;
  reason?: "error" | "slow";
  conversationId?: string | null;
}

export const ALLOWED_FIELDS = [
  "name", "mode", "bucket", "queryHash", "queryLength", "outcome", "ttftMs", "answerChars", "reason", "conversationId",
] as const;

// TODO: a deterministic, well-spread 0-99 bucket per user id (same id -> same bucket on every
// device and render; about N% of users fall below N).
export function bucketOf(userId: string): number {
  void userId;
  return 0;
}

// TODO: kill switch wins over everything; users whose bucket is below percent get flags.mode,
// everyone else gets "off". Clamp percent to 0-100.
export function modeFor(userId: string, flags: FlagValues): Mode {
  void userId;
  return flags.mode;
}

// TODO: the query text must never leave the browser in analytics. Return a stable hash.
export function hashQuery(q: string): string {
  return q;
}
