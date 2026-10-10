// Settings for the help desk triage Lambda (invoked synchronously from the inbound flow).
export const MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0";
export const GUARDRAIL_ID = "gr-lfg-helpdesk-triage";
export const GUARDRAIL_VERSION = "3";
/** Whole-call budget. The flow's InvocationTimeLimitSeconds is 4; leave headroom for cold start and the flow. */
export const BUDGET_MS = 2500;
export const MAX_TOKENS = 300;
export const CATEGORIES = ["password_reset", "access_request", "hardware", "software", "outage", "other"] as const;
export const PRIORITIES = ["P1", "P2", "P3", "P4"] as const;
export type Category = (typeof CATEGORIES)[number];
export type Priority = (typeof PRIORITIES)[number];
