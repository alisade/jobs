import { ConverseCommandInput, ConverseCommandOutput } from "@aws-sdk/client-bedrock-runtime";
import { PipelineConfig, SummaryOutcome } from "./types";

export const TOOL_NAME = "record_acw_summary";

/**
 * TODO: the Converse request (see README "Model call"): system prompt that treats the transcript
 * as untrusted data, the transcript in a delimited block, a forced tool call whose JSON schema
 * requires every AcwSummary field, the guardrail with trace enabled, temperature 0, maxTokens.
 */
export function buildConverseInput(redactedTranscript: string, cfg: PipelineConfig): ConverseCommandInput {
  return { modelId: cfg.modelId, messages: [{ role: "user", content: [{ text: redactedTranscript }] }] };
}

/** TODO: map stopReason and the tool call to OK / GUARDRAIL_BLOCKED / INVALID_OUTPUT (validate every field). */
export function parseConverseOutput(out: ConverseCommandOutput): SummaryOutcome {
  throw new Error(`TODO: parseConverseOutput (stopReason ${out.stopReason})`);
}
