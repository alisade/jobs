import * as fs from "fs";
import * as path from "path";
import { mockClient } from "aws-sdk-client-mock";
import { BedrockRuntimeClient, ConverseCommand } from "@aws-sdk/client-bedrock-runtime";
import { BedrockAgentRuntimeClient, RetrieveCommand } from "@aws-sdk/client-bedrock-agent-runtime";
import { ConnectClient, GetContactAttributesCommand, UpdateContactAttributesCommand } from "@aws-sdk/client-connect";
import { ClaimResult, IdempotencyStore } from "../src/idempotency";
import { ContactEvent, PipelineConfig, Turn } from "../src/types";

export const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
const J = (p: string) => JSON.parse(fs.readFileSync(path.join(root, p), "utf8"));
export const config: PipelineConfig = J("config/pipeline.json");
export const cid = (n: number) => `a1c2d3e4-${String(n).padStart(4, "0")}-4f00-8a00-${String(n).padStart(12, "0")}`;
export const transcript = (n: number): Turn[] => J(`fixtures/transcripts/${cid(n)}.json`);
export const converse = (n: number) => J(`fixtures/bedrock/converse-${cid(n)}.json`);
export const event = (name: string): ContactEvent => J(`fixtures/events/${name}.json`);
export const retrieveMfa = () => J("fixtures/kb/retrieve-mfa.json");
export const evalCases = () => J("fixtures/eval/cases.json");

/** In-memory IdempotencyStore with the same semantics as the DynamoDB one. */
export class MemoryStore implements IdempotencyStore {
  items = new Map<string, { status: string; result?: unknown }>();
  calls: string[] = [];
  async claim(key: string): Promise<ClaimResult> {
    this.calls.push(`claim:${key}`);
    const cur = this.items.get(key);
    if (!cur) { this.items.set(key, { status: "IN_PROGRESS" }); return "CLAIMED"; }
    return cur.status === "COMPLETED" ? "COMPLETED" : "IN_PROGRESS";
  }
  async complete(key: string, result: Record<string, unknown>) { this.calls.push(`complete:${key}`); this.items.set(key, { status: "COMPLETED", result }); }
  async release(key: string) { this.calls.push(`release:${key}`); const c = this.items.get(key); if (c && c.status === "IN_PROGRESS") this.items.delete(key); }
}

export function setup(opts: { attrs?: Record<string, Record<string, string>>; missingTranscripts?: number[] } = {}) {
  const bedrock = mockClient(BedrockRuntimeClient);
  const agent = mockClient(BedrockAgentRuntimeClient);
  const connect = mockClient(ConnectClient);
  // Route each Converse call to the recorded response whose transcript it carries.
  bedrock.on(ConverseCommand).callsFake((input: any) => {
    const body = JSON.stringify(input.messages);
    for (const m of [1, 2, 3, 4]) if (body.includes(transcript(m)[1].text.slice(0, 30))) return converse(m);
    throw Object.assign(new Error("no fixture for this transcript"), { name: "ValidationException" });
  });
  agent.on(RetrieveCommand).resolves(retrieveMfa());
  const attrs = opts.attrs || { [cid(1)]: { snIncidentSysId: "9f1e0000000000000000000000000001" }, [cid(2)]: { snIncidentSysId: "9f1e0000000000000000000000000002" } };
  connect.on(GetContactAttributesCommand).callsFake((input: any) => ({ Attributes: attrs[input.InitialContactId] || {} }));
  connect.on(UpdateContactAttributesCommand).resolves({});
  const notes: { sysId: string; note: string }[] = [];
  const workNotes = { addWorkNote: async (sysId: string, note: string) => { notes.push({ sysId, note }); } };
  const store = new MemoryStore();
  const missing = new Set((opts.missingTranscripts || [5]).map(cid));
  const transcripts = { get: async (id: string) => (missing.has(id) ? null : fs.existsSync(path.join(root, `fixtures/transcripts/${id}.json`)) ? J(`fixtures/transcripts/${id}.json`) : null) };
  const logs: Record<string, unknown>[] = [];
  const deps = {
    config, bedrock: new BedrockRuntimeClient({ region: "us-east-1" }), agentRuntime: new BedrockAgentRuntimeClient({ region: "us-east-1" }),
    connect: new ConnectClient({ region: "us-east-1" }), transcripts, workNotes, idempotency: store, log: (r: Record<string, unknown>) => logs.push(r),
  };
  return { bedrock, agent, connect, notes, store, deps, logs, workNotes };
}
