// lfg-contact-summary: summarizes the caller's self-service conversation for the agent screen pop.
// Invoked synchronously from the inbound flow right before the transfer to queue.
// Contract: ALWAYS answer inside the flow's budget; a degraded answer beats Connect's error branch.
import { BedrockRuntimeClient, ConverseCommand, ConverseCommandOutput } from "@aws-sdk/client-bedrock-runtime";
import { makeClient } from "./client";

export type Deps = { client: BedrockRuntimeClient; flowBudgetMs?: number; maxTokens?: number; modelId?: string; log?: (o: object) => void };
export type ContextLike = { getRemainingTimeInMillis(): number };

export const SYSTEM = "Summarize the caller's IT help desk self-service conversation for the agent in at most three short sentences. No personal data.";
/** Time kept back for returning the response and the flow's own overhead. */
const SAFETY_MS = 300;
const MAX_TOKENS_CAP = 400;

export function buildHandler(deps: Deps) {
  const modelId = deps.modelId || process.env.MODEL_ID || "us.anthropic.claude-haiku-4-5-20251001-v1:0";
  const flowBudgetMs = deps.flowBudgetMs || Number(process.env.FLOW_BUDGET_MS || 6500);
  const maxTokens = Math.min(deps.maxTokens || Number(process.env.MAX_TOKENS || 350), MAX_TOKENS_CAP);
  const log = deps.log || ((o: object) => console.log(JSON.stringify(o)));

  return async function handler(event: any, context: ContextLike): Promise<Record<string, string>> {
    const transcript = String(event?.Details?.ContactData?.Attributes?.lexTranscript || "").slice(0, 6000);
    const t0 = Date.now();
    const deadlineMs = Math.max(0, Math.min(flowBudgetMs, context.getRemainingTimeInMillis()) - SAFETY_MS);
    if (!transcript) return { summaryStatus: "DEGRADED", summary: "", degradedReason: "empty" };

    const controller = new AbortController();
    let timer: NodeJS.Timeout | undefined;
    const deadline = new Promise<"deadline">((resolve) => {
      timer = setTimeout(() => {
        controller.abort();
        resolve("deadline");
      }, deadlineMs);
    });
    try {
      const call = deps.client.send(
        new ConverseCommand({
          modelId,
          system: [{ text: SYSTEM }],
          messages: [{ role: "user", content: [{ text: transcript }] }],
          inferenceConfig: { maxTokens, temperature: 0 },
        }),
        { abortSignal: controller.signal },
      );
      call.catch(() => undefined); // the losing side of the race must not become an unhandled rejection
      const res = await Promise.race([call, deadline]);
      if (res === "deadline") {
        log({ level: "WARN", msg: "summary degraded", reason: "timeout", deadlineMs, elapsedMs: Date.now() - t0 });
        return { summaryStatus: "DEGRADED", summary: "", degradedReason: "timeout" };
      }
      const out = res as ConverseCommandOutput;
      const text = (out.output?.message?.content || []).map((c: any) => c.text || "").join("").replace(/\s+/g, " ").trim();
      log({ level: "INFO", msg: "converse ok", attempts: out.$metadata.attempts, totalRetryDelayMs: out.$metadata.totalRetryDelay, outputTokens: out.usage?.outputTokens, elapsedMs: Date.now() - t0 });
      return { summaryStatus: "OK", summary: text.slice(0, 1000), degradedReason: "" };
    } catch (err: any) {
      const reason = err?.name === "ThrottlingException" || err?.$metadata?.httpStatusCode === 429 ? "throttled" : "error";
      log({ level: "WARN", msg: "summary degraded", reason, error: err?.name, elapsedMs: Date.now() - t0 });
      return { summaryStatus: "DEGRADED", summary: "", degradedReason: reason };
    } finally {
      if (timer) clearTimeout(timer);
    }
  };
}

export const handler = buildHandler({ client: makeClient() });
