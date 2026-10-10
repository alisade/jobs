// Fake of the ContactEventSource adapter (agent workspace SDK ContactClient subset) for tests.
import * as fs from "fs";
import * as path from "path";
import { act } from "@testing-library/react";

const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
export const fixture = (f: string) => JSON.parse(fs.readFileSync(path.join(root, f), "utf8"));
// eslint-disable-next-line @typescript-eslint/no-var-requires
export const appMod = require(path.join(root, "src/AgentAssistApp")) as typeof import("../src/AgentAssistApp");
// eslint-disable-next-line @typescript-eslint/no-var-requires
export const rankMod = require(path.join(root, "src/rank")) as typeof import("../src/rank");
// eslint-disable-next-line @typescript-eslint/no-var-requires
export const apiMod = require(path.join(root, "src/api")) as typeof import("../src/api");
// eslint-disable-next-line @typescript-eslint/no-var-requires
export const guideMod = require(path.join(root, "src/guide")) as typeof import("../src/guide");
export const guides = fixture("guides/guides.json");

type H = (e: any) => any;
export class FakeContactClient {
  connected = new Set<H>();
  cleared = new Set<H>();
  attributes: Record<string, Record<string, string>> = {};
  getAttributesCalls: { contactId: string; keys: string[] | "*" }[] = [];
  onConnected(h: H) { this.connected.add(h); }
  offConnected(h: H) { this.connected.delete(h); }
  onCleared(h: H) { this.cleared.add(h); }
  offCleared(h: H) { this.cleared.delete(h); }
  async getAttributes(contactId: string, keys: string[] | "*") {
    this.getAttributesCalls.push({ contactId, keys });
    const all = this.attributes[contactId] || {};
    if (keys === "*") return { ...all };
    return Object.fromEntries(Object.entries(all).filter(([k]) => keys.includes(k)));
  }
  async connect(contactId: string, attrs: Record<string, string>, type = "chat") {
    this.attributes[contactId] = attrs;
    await act(async () => {
      for (const h of [...this.connected]) await h({ contactId, initialContactId: contactId, type, subtype: type === "voice" ? "connect:Telephony" : "connect:Chat" });
    });
  }
  async clear(contactId: string, type = "chat") {
    await act(async () => {
      for (const h of [...this.cleared]) await h({ contactId, initialContactId: contactId, type, subtype: "connect:Chat" });
    });
  }
}

export const resetHandoff = (over: Record<string, string> = {}) => ({
  botSummary: "Employee locked out after a phone change; asked to reset the password and re-register MFA.",
  lexIntent: "ResetPassword",
  lexSlots: JSON.stringify({ accountType: "standard", device: "new phone", employeeId: "E10442" }),
  incidentNumber: "INC0012345",
  incidentSysId: "0a1b2c3d4e5f60718293a4b5c6d7e8f9",
  callerVerified: "true",
  vip: "false",
  channel: "chat",
  ssn: "123-45-6789",
  ...over,
});

export function fakeApi(fail = false) {
  const calls: { sysId: string; update: any }[] = [];
  return {
    calls,
    async updateIncident(sysId: string, update: any) {
      calls.push({ sysId, update });
      if (fail) throw new Error("incident update failed (503)");
      return { number: "INC0012345", state: "6" };
    },
  };
}
