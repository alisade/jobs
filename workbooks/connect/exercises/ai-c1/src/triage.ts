// Help desk triage Lambda helper (first version from the hackathon). It works in the demo.
// Harden it to the contract in README.md.
import { BedrockRuntimeClient, ConverseCommand } from "@aws-sdk/client-bedrock-runtime";
import { MODEL_ID, MAX_TOKENS, Category, Priority } from "./config";

export type Triage = {
  category: Category;
  priority: Priority;
  summary: string;
  needsHuman: boolean;
  source: "model" | "fallback";
  reason?: "timeout" | "error" | "guardrail" | "invalid_output" | "suspected_injection";
};

export const SYSTEM_PROMPT = "You triage IT help desk calls. Reply with JSON: category, priority, summary, needsHuman.";

export function fallback(reason: Triage["reason"]): Triage {
  return { category: "other", priority: "P3", summary: "", needsHuman: true, source: "fallback", reason };
}

export function buildRequest(transcript: string) {
  return {
    modelId: MODEL_ID,
    system: [{ text: `${SYSTEM_PROMPT}\nCaller said: ${transcript}` }],
    messages: [{ role: "user" as const, content: [{ text: "Triage this call." }] }],
    inferenceConfig: { maxTokens: MAX_TOKENS * 4, temperature: 0.7 },
  };
}

export function parseOutput(text: string): Omit<Triage, "source" | "reason"> | null {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export function applyGuards(t: Omit<Triage, "source" | "reason">, _transcript: string): Triage {
  return { ...t, source: "model" };
}

export async function triage(transcript: string, client: BedrockRuntimeClient, _budgetMs = 2500): Promise<Triage> {
  const res = await client.send(new ConverseCommand(buildRequest(transcript)));
  const text = res.output?.message?.content?.[0]?.text || "";
  const parsed = parseOutput(text);
  if (!parsed) return fallback("invalid_output");
  return applyGuards(parsed, transcript);
}

export function toConnectAttributes(t: Triage): Record<string, any> {
  return t;
}
