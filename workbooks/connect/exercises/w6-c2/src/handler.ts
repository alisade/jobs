import { BedrockRuntimeClient, ConverseCommand } from "@aws-sdk/client-bedrock-runtime";
import { BedrockAgentRuntimeClient } from "@aws-sdk/client-bedrock-agent-runtime";
import { ConnectClient, GetContactAttributesCommand, UpdateContactAttributesCommand } from "@aws-sdk/client-connect";
import { IdempotencyStore } from "./idempotency";
import { relatedArticles } from "./knowledge";
import { redactPii } from "./redact";
import { buildConverseInput, parseConverseOutput } from "./summarize";
import { toTranscriptText } from "./transcript";
import { AcwSummary, Article, ContactEvent, PipelineConfig, PipelineResult, RetryableError, TranscriptSource } from "./types";

export interface Deps {
  config: PipelineConfig;
  bedrock: BedrockRuntimeClient;
  agentRuntime: BedrockAgentRuntimeClient;
  connect: ConnectClient;
  transcripts: TranscriptSource;
  workNotes: { addWorkNote(incidentSysId: string, note: string): Promise<void> };
  idempotency: IdempotencyStore;
  log?: (rec: Record<string, unknown>) => void;
}

const CHANNELS = ["VOICE", "CHAT"];

function redactSummary(s: AcwSummary): AcwSummary {
  const r = (x: string) => redactPii(x).text;
  return { issue: r(s.issue), actionsTaken: s.actionsTaken.map(r), resolution: r(s.resolution), followUps: s.followUps.map(r), sentiment: s.sentiment };
}

export function formatWorkNote(contactId: string, modelId: string, s: AcwSummary, articles: Article[]): string {
  return [
    `[acw-summary contact=${contactId} model=${modelId}]`,
    `Issue: ${s.issue}`,
    "Actions taken:",
    ...s.actionsTaken.map((a) => `- ${a}`),
    `Resolution: ${s.resolution}`,
    "Follow-ups:",
    ...(s.followUps.length ? s.followUps.map((f) => `- ${f}`) : ["- none"]),
    `Sentiment: ${s.sentiment}`,
    "Related KB:",
    ...(articles.length ? articles.map((a) => `- ${a.title} (${a.uri})`) : ["- none"]),
  ].join("\n");
}

/**
 * TODO: the pipeline (README "Handler"): accept only aws.connect DISCONNECTED events for VOICE/CHAT
 * (any casing, any detail-type spelling); claim `acw#<contactId>` in the idempotency store (COMPLETED
 * -> DUPLICATE, IN_PROGRESS -> RetryableError IN_PROGRESS); transcript (null -> RetryableError
 * TRANSCRIPT_NOT_READY); redact; Converse; parse; for OK redact the summary again, retrieve KB
 * articles with the summary issue, write the work note when the contact has snIncidentSysId;
 * update contact attributes; complete the claim. On any failure release the claim and rethrow
 * (Bedrock and ServiceNow failures as RetryableError DOWNSTREAM).
 */
export function makeHandler(deps: Deps) {
  void [ConverseCommand, GetContactAttributesCommand, UpdateContactAttributesCommand, relatedArticles, redactPii, buildConverseInput, parseConverseOutput, toTranscriptText, RetryableError, redactSummary];
  return async function handler(event: ContactEvent): Promise<PipelineResult> {
    throw new Error(`TODO: handle ${event.detail && event.detail.eventType} with ${deps.config.modelId}`);
  };
}
