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

export function makeHandler(deps: Deps) {
  const log = deps.log || (() => undefined);
  const cfg = deps.config;
  return async function handler(event: ContactEvent): Promise<PipelineResult> {
    const d = event && event.detail;
    if (!d || event.source !== "aws.connect" || d.eventType !== "DISCONNECTED" || !CHANNELS.includes(String(d.channel).toUpperCase())) {
      return { status: "IGNORED" };
    }
    const contactId = d.contactId;
    const instanceId = d.instanceArn.split("/").pop() || cfg.instanceId;
    const key = `acw#${contactId}`;
    const claim = await deps.idempotency.claim(key);
    if (claim === "COMPLETED") {
      log({ msg: "duplicate event skipped", contactId });
      return { status: "DUPLICATE", contactId };
    }
    if (claim === "IN_PROGRESS") throw new RetryableError("IN_PROGRESS", `contact ${contactId} is being processed`);
    try {
      const turns = await deps.transcripts.get(contactId);
      if (!turns) throw new RetryableError("TRANSCRIPT_NOT_READY");
      const red = redactPii(toTranscriptText(turns));
      let out;
      try {
        out = await deps.bedrock.send(new ConverseCommand(buildConverseInput(red.text, cfg)));
      } catch (err) {
        throw new RetryableError("DOWNSTREAM", `bedrock: ${(err as Error).name}`);
      }
      const parsed = parseConverseOutput(out);
      const attrs = await deps.connect.send(new GetContactAttributesCommand({ InstanceId: instanceId, InitialContactId: contactId }));
      const sysId = attrs.Attributes && attrs.Attributes.snIncidentSysId;
      let articles: Article[] = [];
      let wroteWorkNote = false;
      const update: Record<string, string> = { acwSummaryStatus: parsed.status };
      if (parsed.status === "OK") {
        const summary = redactSummary(parsed.summary);
        articles = await relatedArticles(deps.agentRuntime, cfg, summary.issue);
        if (sysId) {
          try {
            await deps.workNotes.addWorkNote(sysId, formatWorkNote(contactId, cfg.modelId, summary, articles));
          } catch (err) {
            throw new RetryableError("DOWNSTREAM", `servicenow: ${(err as Error).message}`);
          }
          wroteWorkNote = true;
        }
        update.acwSummaryIssue = summary.issue.slice(0, cfg.attributeMaxChars);
        update.acwSentiment = summary.sentiment;
      }
      await deps.connect.send(new UpdateContactAttributesCommand({ InstanceId: instanceId, InitialContactId: contactId, Attributes: update }));
      const result: PipelineResult = { status: parsed.status, contactId, articles: articles.length, wroteWorkNote };
      await deps.idempotency.complete(key, { status: parsed.status, wroteWorkNote });
      log({ msg: "acw summary done", contactId, status: parsed.status, redactedEntities: red.entities, latencyMs: out.metrics?.latencyMs, tokens: out.usage?.totalTokens });
      return result;
    } catch (err) {
      await deps.idempotency.release(key);
      throw err;
    }
  };
}
