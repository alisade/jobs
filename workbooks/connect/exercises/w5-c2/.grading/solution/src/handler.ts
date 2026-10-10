// Reference solution: Connect flow Lambda (AWS Lambda function block, STRING_MAP response).
import { BedrockAgentRuntimeClient } from "@aws-sdk/client-bedrock-agent-runtime";
import { BedrockRuntimeClient } from "@aws-sdk/client-bedrock-runtime";
import type { ConnectContactFlowEvent } from "aws-lambda";
import config from "../config/rag.json";
import { createAnswerer, RagDeps } from "./rag";
import { ConnectResult, Entitlements, RagConfig } from "./types";

/** SDK clients sized for a voice turn: at most one retry, so retries cannot blow Connect's 8 s budget. */
export function makeClients(region = process.env.AWS_REGION || "us-east-1") {
  return {
    agentRuntime: new BedrockAgentRuntimeClient({ region, maxAttempts: 2 }),
    runtime: new BedrockRuntimeClient({ region, maxAttempts: 2 }),
  };
}

export function entitlementsFrom(attrs: Record<string, string | undefined>): Entitlements {
  return {
    callerVerified: attrs.callerVerified === "true",
    department: attrs.department || "",
    region: attrs.region || "us",
    employeeType: attrs.employeeType === "contractor" ? "contractor" : "employee",
  };
}

export function createHandler(deps: RagDeps) {
  const answer = createAnswerer(deps);
  return async function handler(event: ConnectContactFlowEvent): Promise<ConnectResult> {
    const attrs = (event.Details?.ContactData?.Attributes || {}) as Record<string, string>;
    const question = String(event.Details?.Parameters?.question || "");
    const channel = event.Details?.ContactData?.Channel || "VOICE";
    const r = await answer(question, entitlementsFrom(attrs));
    if (r.status === "ANSWERED") {
      const answerText = channel === "CHAT" ? `${r.answer} (Sources: ${r.citations.join(", ")})` : r.answer;
      return { status: "ANSWERED", answer: answerText.slice(0, 1000), citations: r.citations.join(","), latencyMs: String(r.latencyMs) };
    }
    return { status: "HANDOFF", handoffReason: r.reason, handoffDetail: (r.detail || "").slice(0, 200), latencyMs: String(r.latencyMs) };
  };
}

let cached: ReturnType<typeof createHandler> | undefined;
export const handler = (event: ConnectContactFlowEvent) => {
  cached = cached || createHandler({ ...makeClients(), config: config as RagConfig });
  return cached(event);
};
