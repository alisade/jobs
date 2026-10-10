// Replay client: answers ConverseCommand from recorded responses in fixtures/converse/<caseId>.json,
// matched by the transcript text found in the request messages. Used by `make eval` and the tests.
// Recorded 2026-10-02 against us.anthropic.claude-haiku-4-5-20251001-v1:0 with guardrail gr-lfg-helpdesk-triage v3.
import * as fs from "fs";
import * as path from "path";
import { mockClient } from "aws-sdk-client-mock";
import { BedrockRuntimeClient, ConverseCommand } from "@aws-sdk/client-bedrock-runtime";

export type EvalCase = {
  id: string;
  transcript: string;
  expected: { category: string; maxPriority?: string; allowFallback?: boolean };
  tags: string[];
};

export function loadCases(root: string): EvalCase[] {
  return fs.readFileSync(path.join(root, "eval/cases.jsonl"), "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));
}

/** A BedrockRuntimeClient whose Converse calls are answered from fixtures. */
export function replayClient(root: string, opts: { delayMs?: number } = {}) {
  const cases = loadCases(root);
  const client = new BedrockRuntimeClient({ region: "us-east-1", credentials: { accessKeyId: "x", secretAccessKey: "x" } });
  const mock = mockClient(client);
  mock.on(ConverseCommand).callsFake(async (input: any) => {
    const all = JSON.stringify(input);
    const hit = cases.find((c) => all.includes(JSON.stringify(c.transcript).slice(1, 41)));
    if (!hit) throw Object.assign(new Error("ValidationException: no recorded response for this input"), { name: "ValidationException" });
    if (opts.delayMs) await new Promise((r) => setTimeout(r, opts.delayMs));
    return JSON.parse(fs.readFileSync(path.join(root, "fixtures/converse", `${hit.id}.json`), "utf8"));
  });
  return { client, mock };
}
