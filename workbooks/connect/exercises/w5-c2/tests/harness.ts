// Test harness for connect/w5-c2: recorded Bedrock responses replayed through aws-sdk-client-mock.
import * as fs from "fs";
import * as path from "path";
import { mockClient } from "aws-sdk-client-mock";
import { BedrockAgentRuntimeClient, RetrieveCommand } from "@aws-sdk/client-bedrock-agent-runtime";
import { BedrockRuntimeClient, ConverseCommand } from "@aws-sdk/client-bedrock-runtime";
import type { ConnectContactFlowEvent } from "aws-lambda";
import { createHandler } from "../src/handler";
import { RagConfig } from "../src/types";

const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
export const fx = (name: string) => JSON.parse(fs.readFileSync(path.join(root, "tests/fixtures", `${name}.json`), "utf8"));
export const baseConfig: RagConfig = JSON.parse(fs.readFileSync(path.join(root, "config/rag.json"), "utf8"));

export const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export type Setup = { retrieve?: string | Error; converse?: string | Error; retrieveDelayMs?: number; converseDelayMs?: number; config?: Partial<RagConfig> };

export function setup(s: Setup = {}) {
  const agentRuntime = new BedrockAgentRuntimeClient({ region: "us-east-1" });
  const runtime = new BedrockRuntimeClient({ region: "us-east-1" });
  const ar = mockClient(agentRuntime);
  const rt = mockClient(runtime);
  ar.on(RetrieveCommand).callsFake(async () => {
    if (s.retrieveDelayMs) await sleep(s.retrieveDelayMs);
    if (s.retrieve instanceof Error) throw s.retrieve;
    return fx(s.retrieve || "retrieve-vpn");
  });
  rt.on(ConverseCommand).callsFake(async () => {
    if (s.converseDelayMs) await sleep(s.converseDelayMs);
    if (s.converse instanceof Error) throw s.converse;
    return fx(s.converse || "converse-vpn-ok");
  });
  const handler = createHandler({ agentRuntime, runtime, config: { ...baseConfig, ...(s.config || {}) } });
  return { handler, ar, rt };
}

export function event(attrs: Record<string, string>, question = "how do I re-enroll my VPN token", channel = "VOICE"): ConnectContactFlowEvent {
  return {
    Name: "ContactFlowEvent",
    Details: {
      ContactData: {
        Attributes: attrs, Channel: channel as any, ContactId: "4a573372-1f28-4e26-b97b-6c1d2e3f4a5b", InitialContactId: "4a573372-1f28-4e26-b97b-6c1d2e3f4a5b",
        InitiationMethod: "INBOUND", InstanceARN: "arn:aws:connect:us-east-1:111122223333:instance/5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f",
        PreviousContactId: "", Queue: null, SystemEndpoint: { Address: "+18005550142", Type: "TELEPHONE_NUMBER" },
        CustomerEndpoint: { Address: "+15555550100", Type: "TELEPHONE_NUMBER" }, MediaStreams: { Customer: { Audio: null } },
      } as any,
      Parameters: { question },
    },
  } as ConnectContactFlowEvent;
}

export const FINANCE = { callerVerified: "true", department: "Finance", region: "uk", employeeType: "employee" };
export const CONTRACTOR = { callerVerified: "true", department: "IT", region: "in", employeeType: "contractor" };
export const UNVERIFIED = { callerVerified: "false" };

export function sentRetrieve(ar: ReturnType<typeof mockClient>) {
  return ar.commandCalls(RetrieveCommand)[0]?.args[0].input as any;
}
export function sentConverse(rt: ReturnType<typeof mockClient>) {
  return rt.commandCalls(ConverseCommand)[0]?.args[0].input as any;
}
