// Type declarations for connect-kit (plain CommonJS JavaScript).

export type FlowAction = {
  Identifier: string;
  Type: string;
  Parameters: Record<string, any>;
  Transitions: {
    NextAction?: string;
    Conditions?: { NextAction: string; Condition: { Operator: string; Operands: string[] } }[];
    Errors?: { NextAction: string; ErrorType: string }[];
  };
};
export type Flow = { Version: string; StartAction: string; Metadata?: any; Actions: FlowAction[] };

export type FlowIssue = { code: string; severity: "error" | "warning"; actionId: string | null; message: string };
export function validateFlow(flow: Flow, options?: { knownAttributes?: string[]; queueFlow?: boolean }): { ok: boolean; issues: FlowIssue[] };

export type LambdaFake = (payload: any) => Record<string, any> | { __error: string };
export type Scenario = {
  channel?: "VOICE" | "CHAT" | "TASK";
  customerEndpoint?: string;
  contactId?: string;
  queue?: string;
  attributes?: Record<string, string>;
  inputs?: (string | null)[];
  lambdas?: Record<string, LambdaFake>;
  lambdaLatencyMs?: Record<string, number>;
  hours?: Record<string, boolean>;
  metrics?: Record<string, Record<string, number>>;
  queueAtCapacity?: Record<string, boolean>;
  lex?: ({ intent: string; slots?: Record<string, string>; sessionAttributes?: Record<string, string> } | { error: string })[];
  modules?: Record<string, Flow>;
  maxSteps?: number;
};
export type SimResult = {
  outcome: "Disconnected" | "TransferredToQueue" | "Ended" | "TransferredToFlow" | "DeadEnd" | "StepLimit" | "Error";
  queue: string | null;
  attributes: Record<string, string>;
  external: Record<string, any>;
  routing: { priority?: number; timeAdjustment?: number; criteria?: any };
  trace: { id: string; type: string; branch: string; module?: string }[];
  prompts: string[];
  lambdaCalls: { arn: string; payload: any; latencyMs: number }[];
  steps: number;
  at?: string;
  reason?: string;
  error?: string;
  flowId?: string;
};
export function simulate(flow: Flow, scenario?: Scenario): SimResult;
export const CONNECT_SYNC_LAMBDA_MAX_SECONDS: number;
export const REQUIRED_ERRORS: Record<string, string[]>;
export const KNOWN_TYPES: Set<string>;
export function edges(action: FlowAction): { to: string; kind: string; label: string }[];
export function reachable(flow: Flow): Set<string>;
export function resolveRef(value: string, ctx: any): string;

export type SnRequest = { method: string; path: string; query: Record<string, string>; headers: Record<string, any>; body: string; status: number; ts: number };
export type FakeServiceNow = {
  url: string;
  client: { clientId: string; clientSecret: string };
  db: Record<string, Record<string, any>[]>;
  requests: SnRequest[];
  faults: {
    rateLimit?: number[];
    retryAfterSeconds?: number;
    latencyMs?: number;
    tokenTtlSeconds?: number;
    expireTokensAfter?: number;
    createCommitThenFail?: number[];
    failStatus?: Record<number, number>;
  };
  counters: { table: number; create: number; token: number };
  tableRequests(): SnRequest[];
  stop(): Promise<void>;
};
export function startFakeServiceNow(opts?: {
  seed?: Record<string, Record<string, any>[]>;
  client?: { clientId: string; clientSecret: string };
  faults?: FakeServiceNow["faults"];
}): Promise<FakeServiceNow>;
export function parseQuery(q: string): { clauses: any[]; order: { field: string; desc: boolean }[] };
export const DEFAULT_CLIENT: { clientId: string; clientSecret: string };
