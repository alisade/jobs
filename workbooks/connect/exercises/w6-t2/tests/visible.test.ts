// Visible tests for connect/w6-t2.
import { validateFlow } from "connect-kit";
import { effectiveAtTransfer, inbound, moduleFlow } from "./helpers";

test("the inbound flow and the module pass the graph lint", () => {
  expect(validateFlow(inbound()).issues.filter((i) => i.severity === "error")).toEqual([]);
  expect(validateFlow(moduleFlow()).issues.filter((i) => i.severity === "error")).toEqual([]);
});

test("a caller routed to GeneralSupport still has real-time analytics when the agent picks up", () => {
  const e = effectiveAtTransfer("general");
  expect(e.result.outcome).toBe("TransferredToQueue");
  expect(e.analytics.VoiceAnalyticsBehavior.AnalyticsModes).toContain("RealTime");
});
