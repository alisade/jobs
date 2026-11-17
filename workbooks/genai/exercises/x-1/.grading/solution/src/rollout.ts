// Rollout rules for the storefront assistant: flags, cohorts and the analytics schema. Reference solution.

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

/** 32-bit FNV-1a, as 8 hex digits. */
export function fnv1a(s: string): string {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h.toString(16).padStart(8, "0");
}

/** Stable 0-99 bucket per user id. Salted so this experiment's buckets do not line up with others. */
export function bucketOf(userId: string): number {
  return parseInt(fnv1a("assistant-rollout-v1:" + userId), 16) % 100;
}

export function modeFor(userId: string, flags: FlagValues): Mode {
  if (flags.killSwitch) return "off";
  const pct = Math.max(0, Math.min(100, flags.percent));
  return bucketOf(userId) < pct ? flags.mode : "off";
}

/** Query text never leaves the browser: only a salted hash and the length. */
export function hashQuery(q: string): string {
  return fnv1a("q:" + q.trim().toLowerCase());
}
