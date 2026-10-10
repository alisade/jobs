// Shared test harness for connect/w5-c1: recorded Lex V2 events + in-memory backends.
import * as fs from "fs";
import * as path from "path";
import { createHandler } from "../src/handler";
import { Deps, DirectoryRecord, SystemCode } from "../src/deps";
import { LexEvent, LexResponse } from "../src/lex-types";

const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
export function fixture(name: string): LexEvent {
  return JSON.parse(fs.readFileSync(path.join(root, "tests/fixtures", `${name}.json`), "utf8"));
}

const people: Record<string, DirectoryRecord> = {
  "44129": { employeeId: "44129", displayName: "Dana Whitfield", department: "Finance", status: "LOCKED", mfaEnrolled: true, vip: false },
  "30077": { employeeId: "30077", displayName: "Ravi Menon", department: "Treasury", status: "ACTIVE", mfaEnrolled: false, vip: false },
  "61500": { employeeId: "61500", displayName: "Lee Okafor", department: "Audit", status: "DISABLED", mfaEnrolled: true, vip: false },
};

export type Calls = { lookup: string[]; unlock: string[]; reset: { id: string; system: SystemCode }[] };

export function makeDeps(overrides: Partial<{ resetResult: "SENT" | "NO_MFA" | "FAILED"; throwOn: "lookup" | "reset" }> = {}) {
  const calls: Calls = { lookup: [], unlock: [], reset: [] };
  const deps: Deps = {
    directory: {
      async lookup(id) {
        calls.lookup.push(id);
        if (overrides.throwOn === "lookup") throw new Error("directory timeout");
        return people[id] ? { ...people[id] } : null;
      },
      async unlock(id) {
        calls.unlock.push(id);
        return people[id]?.status === "LOCKED" ? "UNLOCKED" : "NOT_LOCKED";
      },
    },
    reset: {
      async sendResetLink(id, system) {
        calls.reset.push({ id, system });
        if (overrides.throwOn === "reset") throw new Error("reset service 503");
        if (overrides.resetResult) return overrides.resetResult;
        return people[id]?.mfaEnrolled ? "SENT" : "NO_MFA";
      },
    },
  };
  return { deps, calls };
}

export async function run(name: string, overrides = {}): Promise<{ res: LexResponse; calls: Calls; event: LexEvent }> {
  const { deps, calls } = makeDeps(overrides);
  const event = fixture(name);
  const res = await createHandler(deps)(event);
  return { res, calls, event };
}

/** Structural checks every response must pass (Lex rejects the turn otherwise). */
export function assertValidResponse(res: LexResponse): void {
  expect(res.sessionState).toBeDefined();
  const da = res.sessionState.dialogAction;
  expect(["Close", "ConfirmIntent", "Delegate", "ElicitIntent", "ElicitSlot"]).toContain(da.type);
  const attrs = res.sessionState.sessionAttributes || {};
  for (const v of Object.values(attrs)) expect(typeof v).toBe("string");
  expect(Buffer.byteLength(JSON.stringify(attrs))).toBeLessThan(12 * 1024);
  if (da.type === "ElicitSlot") {
    expect(da.slotToElicit).toBeTruthy();
    expect(res.sessionState.intent?.name).toBeTruthy();
  }
  if (da.type === "Close") {
    expect(res.sessionState.intent?.name).toBeTruthy();
    expect(["Failed", "Fulfilled", "InProgress"]).toContain(res.sessionState.intent?.state);
  }
  if (da.type === "ConfirmIntent") {
    expect(res.sessionState.intent?.name).toBeTruthy();
    expect(res.sessionState.intent?.slots).toBeDefined();
    expect(res.messages && res.messages.length).toBeTruthy();
  }
  if (da.type === "ElicitIntent") expect(res.messages && res.messages.length).toBeTruthy();
  for (const m of res.messages || []) expect(["PlainText", "SSML", "CustomPayload", "ImageResponseCard"]).toContain(m.contentType);
}

export const said = (res: LexResponse) => (res.messages || []).map((m) => m.content || "").join(" ");
export const attrsOf = (res: LexResponse) => res.sessionState.sessionAttributes || {};
