// Permission-aware RAG answerer for LFG's help desk: Retrieve (Bedrock knowledge base) + Converse.
// This is the pilot version. See README.md "Requirements" for what it must do before go-live.
import { BedrockAgentRuntimeClient, RetrieveCommand, RetrievalFilter } from "@aws-sdk/client-bedrock-agent-runtime";
import { BedrockRuntimeClient, ConverseCommand } from "@aws-sdk/client-bedrock-runtime";
import { AnswerResult, Entitlements, RagConfig } from "./types";

export type RagDeps = { agentRuntime: BedrockAgentRuntimeClient; runtime: BedrockRuntimeClient; config: RagConfig; now?: () => number };

export const SYSTEM_PROMPT = "You are a helpful IT assistant. Answer the employee's question.";

/** Metadata filter for Retrieve, derived from the caller's entitlements. */
export function buildFilter(e: Entitlements): RetrievalFilter | undefined {
  // TODO: unverified callers see only public-help articles; verified employees see all-workers,
  // all-employees and their own department; contractors see all-workers and contractors only;
  // region global or the caller's region; only published articles.
  void e;
  return undefined;
}

export function createAnswerer(deps: RagDeps) {
  const cfg = deps.config;
  const now = deps.now || (() => Date.now());
  return async function answer(question: string, who: Entitlements): Promise<AnswerResult> {
    const start = now();
    const retrieved = await deps.agentRuntime.send(
      new RetrieveCommand({
        knowledgeBaseId: cfg.knowledgeBaseId,
        retrievalQuery: { text: question },
        retrievalConfiguration: { vectorSearchConfiguration: { numberOfResults: cfg.numberOfResults, filter: buildFilter(who) } },
      }),
    );
    const context = (retrieved.retrievalResults || []).map((r) => r.content?.text || "").join("\n");
    const out = await deps.runtime.send(
      new ConverseCommand({
        modelId: cfg.modelId,
        system: [{ text: SYSTEM_PROMPT }],
        messages: [{ role: "user", content: [{ text: `${context}\n\nQuestion: ${question}` }] }],
        inferenceConfig: { maxTokens: cfg.maxTokens },
      }),
    );
    const text = (out.output?.message?.content || []).map((c: any) => c.text || "").join("");
    return { status: "ANSWERED", answer: text, citations: [], latencyMs: now() - start };
  };
}
