// Connect flow Lambda (AWS Lambda function block, synchronous, STRING_MAP response).
// The flow passes the caller's question as the "question" parameter and reads $.External.status,
// $.External.answer, $.External.citations, $.External.handoffReason.
import { BedrockAgentRuntimeClient } from "@aws-sdk/client-bedrock-agent-runtime";
import { BedrockRuntimeClient } from "@aws-sdk/client-bedrock-runtime";
import type { ConnectContactFlowEvent } from "aws-lambda";
import config from "../config/rag.json";
import { createAnswerer, RagDeps } from "./rag";
import { ConnectResult, Entitlements, RagConfig } from "./types";

export function makeClients(region = process.env.AWS_REGION || "us-east-1") {
  // TODO: size the SDK retry behavior for a voice turn inside Connect's 8 s synchronous limit.
  return { agentRuntime: new BedrockAgentRuntimeClient({ region }), runtime: new BedrockRuntimeClient({ region }) };
}

export function entitlementsFrom(attrs: Record<string, string | undefined>): Entitlements {
  // TODO: map contact attributes to entitlements (see README).
  return { callerVerified: true, department: attrs.department || "", region: attrs.region || "us", employeeType: "employee" };
}

export function createHandler(deps: RagDeps) {
  const answer = createAnswerer(deps);
  return async function handler(event: ConnectContactFlowEvent): Promise<ConnectResult> {
    const attrs = (event.Details?.ContactData?.Attributes || {}) as Record<string, string>;
    const question = String(event.Details?.Parameters?.question || "");
    const r = await answer(question, entitlementsFrom(attrs));
    if (r.status === "ANSWERED") return { status: "ANSWERED", answer: r.answer, citations: r.citations.join(",") };
    return { status: "HANDOFF", handoffReason: r.reason };
  };
}

let cached: ReturnType<typeof createHandler> | undefined;
export const handler = (event: ConnectContactFlowEvent) => {
  cached = cached || createHandler({ ...makeClients(), config: config as RagConfig });
  return cached(event);
};
