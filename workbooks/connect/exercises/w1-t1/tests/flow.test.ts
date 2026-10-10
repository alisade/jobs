// Visible tests for connect/w1-t1.
import { validateFlow } from "connect-kit";
import { call, loadFlow } from "./harness";

test("the flow has no unbounded cycles", () => {
  expect(validateFlow(loadFlow()).issues.filter((i) => i.code === "UNBOUNDED_LOOP")).toEqual([]);
});

test("option 2 reaches GeneralSupport while the PasswordReset team is in training", () => {
  const r = call({ option: "2", staffed: { PasswordReset: 0 } });
  expect(r.outcome).toBe("TransferredToQueue");
  expect(r.queueName).toBe("GeneralSupport");
});
