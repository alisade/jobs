// lfg-contact-summary: summarizes the caller's self-service conversation for the agent screen pop.
// Invoked synchronously from the inbound flow right before the transfer to queue.
import { BedrockRuntimeClient, ConverseCommand } from "@aws-sdk/client-bedrock-runtime";
import { makeClient } from "./client";

export type Deps = { client: BedrockRuntimeClient; flowBudgetMs?: number; maxTokens?: number; modelId?: string; log?: (o: object) => void };
export type ContextLike = { getRemainingTimeInMillis(): number };

export const SYSTEM = "Summarize the caller's IT help desk self-service conversation for the agent in at most three short sentences. No personal data.";

export function buildHandler(deps: Deps) {
  const modelId = deps.modelId || process.env.MODEL_ID || "us.anthropic.claude-haiku-4-5-20251001-v1:0";
  const maxTokens = deps.maxTokens || Number(process.env.MAX_TOKENS || 2048);
  const log = deps.log || ((o: object) => console.log(JSON.stringify(o)));
  return async function handler(event: any, _context: ContextLike): Promise<Record<string, string>> {
    const transcript = event?.Details?.ContactData?.Attributes?.lexTranscript || "";
    const t0 = Date.now();
    const res = await deps.client.send(
      new ConverseCommand({
        modelId,
        system: [{ text: SYSTEM }],
        messages: [{ role: "user", content: [{ text: transcript }] }],
        inferenceConfig: { maxTokens, temperature: 0 },
      }),
    );
    const text = (res.output?.message?.content || []).map((c: any) => c.text || "").join("").trim();
    log({ level: "INFO", msg: "converse ok", attempts: res.$metadata.attempts, totalRetryDelayMs: res.$metadata.totalRetryDelay, outputTokens: res.usage?.outputTokens, elapsedMs: Date.now() - t0 });
    return { summaryStatus: "OK", summary: text, degradedReason: "" };
  };
}

export const handler = buildHandler({ client: makeClient() });
