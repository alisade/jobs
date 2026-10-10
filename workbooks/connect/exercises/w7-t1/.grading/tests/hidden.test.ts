// Hidden tests for connect/w7-t1 (run from tests/__hidden__).
import { validateFlow } from "connect-kit";
import { handoff, chatFlow, handoffModule, res } from "../harness";

const KEYS = ["lexIntent", "botSummary", "lexSlots", "callerVerified", "handoffSource"];

describe("fixed state", () => {
  test.each(["ResetPassword", "VpnIssue", "Escalate"])("chat %s: every handoff attribute populated", (intent) => {
    const r = handoff("CHAT", { intent, summary: `summary for ${intent}`, slots: { a: "1" } });
    expect(r.outcome).toBe("TransferredToQueue");
    expect(r.attributes.lexIntent).toBe(intent);
    expect(r.attributes.botSummary).toBe(`summary for ${intent}`);
    expect(JSON.parse(r.attributes.lexSlots)).toEqual({ a: "1" });
    expect(r.attributes.callerVerified).toBe("true");
    expect(r.attributes.handoffSource).toBe("bot");
  });
  test("chat routing unchanged: ResetPassword -> PasswordReset, others -> GeneralSupport", () => {
    expect(handoff("CHAT", { intent: "ResetPassword" }).queueName).toBe("PasswordReset");
    expect(handoff("CHAT", { intent: "VpnIssue" }).queueName).toBe("GeneralSupport");
  });
  test("voice and chat hand over the same set of context attributes", () => {
    const v = handoff("VOICE", { intent: "VpnIssue" }).attributes;
    const c = handoff("CHAT", { intent: "VpnIssue" }).attributes;
    for (const key of KEYS) {
      expect(c[key]).toBeTruthy();
      expect(c[key]).toBe(v[key]);
    }
  });
  test("an unverified caller stays unverified on chat (no hard-coded value)", () => {
    expect(handoff("CHAT", { intent: "ResetPassword", verified: "false" }).attributes.callerVerified).toBe("false");
  });
});

describe("root cause addressed, not papered over", () => {
  test("a module invoked by the chat flow does not read the caller flow's Lex, Lambda or stored input data", () => {
    const usesModule = chatFlow().Actions.some((a) => a.Type === "InvokeFlowModule" && a.Parameters.FlowModuleId === res.modules["lfg-handoff"]);
    if (!usesModule) return; // inlining the copy is also a valid fix
    const text = JSON.stringify(handoffModule().Actions);
    expect(text).not.toMatch(/\$\.(Lex|External|StoredCustomerInput)\b/);
  });
  test("bot context is copied before any transfer on every chat path that came from the bot", () => {
    const r = handoff("CHAT", { intent: "Escalate" });
    expect(r.trace.findIndex((s) => s.type === "UpdateContactAttributes")).toBeGreaterThanOrEqual(0);
    expect(r.trace.findIndex((s) => s.type === "UpdateContactAttributes")).toBeLessThan(r.trace.findIndex((s) => s.type === "TransferContactToQueue"));
  });
});

describe("guards", () => {
  test("bot timeout on chat still reaches an agent", () => {
    const r = handoff("CHAT", { error: "timeout" });
    expect(r.outcome).toBe("TransferredToQueue");
    expect(r.queueName).toBe("GeneralSupport");
  });
  test("voice ResetPassword still routes to PasswordReset with context", () => {
    const r = handoff("VOICE", { intent: "ResetPassword" });
    expect(r.queueName).toBe("PasswordReset");
    expect(r.attributes.lexIntent).toBe("ResetPassword");
  });
  test("module still lints clean", () => {
    expect(validateFlow(handoffModule()).ok).toBe(true);
  });
});
