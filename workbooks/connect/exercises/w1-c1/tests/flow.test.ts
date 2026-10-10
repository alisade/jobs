// Visible tests for connect/w1-c1. The grader adds more (edge cases, failure paths).
import { validateFlow } from "connect-kit";
import { loadFlow, run } from "./harness";

test("flow passes the structural and graph checks (make lint)", () => {
  const r = validateFlow(loadFlow());
  const errors = r.issues.filter((i) => i.severity === "error").map((i) => `${i.code} ${i.actionId}: ${i.message}`);
  expect(errors).toEqual([]);
});

test("open hours, option 2 goes to GeneralSupport", () => {
  const r = run({ inputs: ["2"] });
  expect(r.outcome).toBe("TransferredToQueue");
  expect(r.queueName).toBe("GeneralSupport");
});

test("open hours, option 1 with a successful reset ends the call without an agent", () => {
  const r = run({ inputs: ["1"], reset: "SENT" });
  expect(r.outcome).toBe("Disconnected");
  expect(r.prompts.join(" ")).toMatch(/reset link has been sent/i);
});

test("after hours, the caller hears the closed message", () => {
  const r = run({ open: false, inputs: [null] });
  expect(r.outcome).toBe("Disconnected");
  expect(r.prompts.join(" ")).toMatch(/closed/i);
});
