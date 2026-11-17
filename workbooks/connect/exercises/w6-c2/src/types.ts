// Shared types for connect/w6-c2 (do not change).

/** EventBridge contact event (documented shape; only the fields used here). The docs show the
 * detail-type both as "Amazon Connect Contact Event" and "Connect Customer Contact Event" after the
 * 2026 rename, so match on source + detail.eventType, never on the detail-type string. */
export interface ContactEvent {
  version: string;
  id: string;
  "detail-type": string;
  source: string;
  account: string;
  time: string;
  region: string;
  resources: string[];
  detail: {
    eventType: string; // INITIATED | CONNECTED_TO_SYSTEM | CONTACT_DATA_UPDATED | QUEUED | CONNECTED_TO_AGENT | DISCONNECTED | PAUSED | RESUMED | COMPLETED
    contactId: string;
    initialContactId?: string;
    channel: string; // documented samples use both "VOICE" and "Voice"
    instanceArn: string;
    initiationMethod?: string;
    disconnectTimestamp?: string;
    agentInfo?: { agentArn: string };
    queueInfo?: { queueArn: string };
  };
}

export interface PipelineConfig {
  instanceId: string;
  modelId: string;
  guardrail: { identifier: string; version: string };
  maxTokens: number;
  knowledgeBaseId: string;
  kbNumberOfResults: number;
  kbMinScore: number;
  kbAudience: string[];
  idempotencyTable: string;
  idempotencyTtlSeconds: number;
  inProgressExpirySeconds: number;
  attributeMaxChars: number;
}

/** The structured after-contact summary the model must produce (via the forced tool call). */
export interface AcwSummary {
  issue: string;
  actionsTaken: string[];
  resolution: string;
  followUps: string[];
  sentiment: "POSITIVE" | "NEUTRAL" | "NEGATIVE" | "MIXED";
}

export type SummaryOutcome =
  | { status: "OK"; summary: AcwSummary }
  | { status: "GUARDRAIL_BLOCKED" }
  | { status: "INVALID_OUTPUT"; reason: string };

export interface Article { title: string; uri: string; score: number }

export interface Turn { participant: "AGENT" | "CUSTOMER"; text: string; beginMillis: number }

/** Where the redacted conversational analytics transcript comes from (S3 in production). */
export interface TranscriptSource {
  /** null when the post-contact analysis is not available yet */
  get(contactId: string): Promise<Turn[] | null>;
}

export interface PipelineResult {
  status: "OK" | "GUARDRAIL_BLOCKED" | "INVALID_OUTPUT" | "IGNORED" | "DUPLICATE";
  contactId?: string;
  articles?: number;
  wroteWorkNote?: boolean;
}

/** Thrown when the event should be retried later (EventBridge/SQS redelivery). */
export class RetryableError extends Error {
  constructor(readonly code: "TRANSCRIPT_NOT_READY" | "IN_PROGRESS" | "DOWNSTREAM", message?: string) {
    super(message || code);
  }
}

export interface EvalReference { keyFacts: string[][] }
export interface EvalResult {
  faithfulness: number; // supported actionsTaken / total, 2 decimals (1 when there are none)
  coverage: number; // key facts present / total, 2 decimals
  hallucinations: string[]; // identifiers in the summary that never appear in the transcript
  pass: boolean;
}
