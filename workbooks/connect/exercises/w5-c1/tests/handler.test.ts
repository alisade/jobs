// Visible tests for connect/w5-c1. The grader adds more (edge cases, failure paths, handoff contract).
import { assertValidResponse, attrsOf, run, said } from "./harness";

test("valid spoken employee id moves on to the system name", async () => {
  const { res } = await run("reset-employee-id-valid");
  assertValidResponse(res);
  expect(res.sessionState.dialogAction).toMatchObject({ type: "ElicitSlot", slotToElicit: "SystemName" });
  expect(res.sessionState.intent?.slots?.EmployeeId?.value?.interpretedValue).toBe("44129");
});

test("a too-short employee id is re-elicited with a clear message", async () => {
  const { res } = await run("reset-employee-id-too-short");
  assertValidResponse(res);
  expect(res.sessionState.dialogAction).toMatchObject({ type: "ElicitSlot", slotToElicit: "EmployeeId" });
  expect(said(res)).toMatch(/five digit/i);
});

test("all slots filled: confirm before resetting", async () => {
  const { res } = await run("reset-system-resolved");
  assertValidResponse(res);
  expect(res.sessionState.dialogAction.type).toBe("ConfirmIntent");
  expect(said(res)).toMatch(/VPN/);
});

test("fulfillment sends the reset link and closes", async () => {
  const { res, calls } = await run("reset-fulfill");
  assertValidResponse(res);
  expect(calls.reset).toEqual([{ id: "44129", system: "VPN" }]);
  expect(res.sessionState.dialogAction.type).toBe("Close");
  expect(res.sessionState.intent?.state).toBe("Fulfilled");
});

test("session attributes from Connect are preserved", async () => {
  const { res } = await run("reset-employee-id-valid");
  expect(attrsOf(res).contactId).toBe("4a573372-1f28-4e26-b97b-6c1d2e3f4a5b");
});
