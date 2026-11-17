// lfg-selfservice-assistant: called by the chat/voice self-service path for each caller turn.
// Converse with a pinned guardrail version; on intervention, hand off to an agent with the reason.
import { BedrockRuntimeClient, ConverseCommand } from "@aws-sdk/client-bedrock-runtime";
import { SYSTEM_PROMPT } from "./prompt";

export interface Turn {
  contactId: string;
  text: string;
}
export interface Reply {
  action: "REPLY" | "HANDOFF";
  text: string;
  reason: string;
}

export interface Config {
  modelId: string;
  guardrailId: string;
  guardrailVersion: string;
}

export function configFromEnv(env: Record<string, string | undefined>): Config {
  return {
    modelId: env.MODEL_ID || "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    guardrailId: env.GUARDRAIL_ID || "",
    guardrailVersion: env.GUARDRAIL_VERSION || "DRAFT",
  };
}

export async function answer(client: BedrockRuntimeClient, cfg: Config, turn: Turn): Promise<Reply> {
  const out = await client.send(new ConverseCommand({
    modelId: cfg.modelId,
    system: [{ text: SYSTEM_PROMPT }],
    messages: [{ role: "user", content: [{ text: turn.text }] }],
    inferenceConfig: { maxTokens: 300, temperature: 0 },
    guardrailConfig: { guardrailIdentifier: cfg.guardrailId, guardrailVersion: cfg.guardrailVersion, trace: "enabled" },
  }));
  const text = (out.output?.message?.content || []).map((c: any) => c.text || "").join("");
  // guardrail_intervened also covers ANONYMIZE (masked PII, conversation continues): only a BLOCK hands off.
  const blocked = JSON.stringify((out as any).trace?.guardrail || {}).includes('"BLOCKED"');
  if (out.stopReason === "guardrail_intervened" && blocked) return { action: "HANDOFF", text, reason: "guardrail" };
  return { action: "REPLY", text, reason: "" };
}
