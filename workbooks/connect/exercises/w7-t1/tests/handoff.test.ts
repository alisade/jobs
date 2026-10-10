// Visible tests for connect/w7-t1.
import { validateFlow } from "connect-kit";
import { handoff, voiceFlow, chatFlow, handoffModule } from "./harness";

test("flows and module pass the graph lint", () => {
  for (const f of [voiceFlow(), chatFlow(), handoffModule()]) expect(validateFlow(f).issues.filter((i) => i.severity === "error")).toEqual([]);
});

test("voice: the agent receives the bot context", () => {
  const r = handoff("VOICE", { intent: "ResetPassword" });
  expect(r.outcome).toBe("TransferredToQueue");
  expect(r.attributes.lexIntent).toBe("ResetPassword");
  expect(r.attributes.botSummary).toMatch(/Locked out/);
});

test("chat: the agent receives the bot context", () => {
  const r = handoff("CHAT", { intent: "ResetPassword" });
  expect(r.outcome).toBe("TransferredToQueue");
  expect(r.attributes.lexIntent).toBe("ResetPassword");
  expect(r.attributes.botSummary).toMatch(/Locked out/);
});
