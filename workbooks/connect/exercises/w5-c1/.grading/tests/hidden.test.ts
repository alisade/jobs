// Hidden tests for connect/w5-c1 (run from tests/__hidden__).
import { assertValidResponse, attrsOf, fixture, makeDeps, run, said } from "../harness";
import { createHandler, normalizeEmployeeId } from "../../src/handler";

describe("employee id", () => {
  test.each([["44129", "44129"], ["E44129", "44129"], ["E 44129", "44129"], ["e-44129", "44129"], [" 44129 ", "44129"], ["4412", null], ["441299", null], ["ABCDE", null], [undefined, null]])(
    "normalizeEmployeeId(%p) -> %p", (input, out) => { expect(normalizeEmployeeId(input as any)).toBe(out); });

  test("DTMF entry is accepted", async () => {
    const { res } = await run("reset-employee-id-dtmf");
    assertValidResponse(res);
    expect(res.sessionState.dialogAction).toMatchObject({ type: "ElicitSlot", slotToElicit: "SystemName" });
  });
  test("an E-prefixed id is normalized into the slot", async () => {
    const { res } = await run("reset-employee-id-with-prefix");
    expect(res.sessionState.intent?.slots?.EmployeeId?.value?.interpretedValue).toBe("44129");
  });
  test("an invalid id clears the slot and counts the attempt", async () => {
    const { res } = await run("reset-employee-id-too-short");
    expect(res.sessionState.intent?.slots?.EmployeeId ?? null).toBeNull();
    expect(attrsOf(res).employeeIdAttempts).toBe("1");
  });
  test("an unknown id is re-elicited, not accepted", async () => {
    const { res, calls } = await run("reset-employee-id-unknown");
    assertValidResponse(res);
    expect(calls.lookup).toContain("55555");
    expect(res.sessionState.dialogAction).toMatchObject({ type: "ElicitSlot", slotToElicit: "EmployeeId" });
  });
  test("second invalid attempt hands off to an agent with context", async () => {
    const { res } = await run("reset-employee-id-invalid-second");
    assertValidResponse(res);
    expect(res.sessionState.dialogAction.type).toBe("Close");
    expect(res.sessionState.intent?.state).toBe("Failed");
    const a = attrsOf(res);
    expect(a.handoff).toBe("true");
    expect(a.handoffReason).toBe("EMPLOYEE_ID_INVALID");
    expect(a.handoffQueue).toBe("GeneralSupport");
  });
  test("a verified caller from Connect is not asked for the id again", async () => {
    const { res, calls } = await run("reset-verified-caller-initial");
    assertValidResponse(res);
    expect(res.sessionState.dialogAction).toMatchObject({ type: "ElicitSlot", slotToElicit: "SystemName" });
    expect(res.sessionState.intent?.slots?.EmployeeId?.value?.interpretedValue).toBe("44129");
    expect(calls.lookup).toEqual(["44129"]);
  });
  test("an unverified caller with no id is asked for it", async () => {
    const { res } = await run("reset-initial-no-slots");
    assertValidResponse(res);
    expect(res.sessionState.dialogAction).toMatchObject({ type: "ElicitSlot", slotToElicit: "EmployeeId" });
  });
});

describe("system name resolution", () => {
  test("uses the resolved canonical value, not the raw words", async () => {
    const { res } = await run("reset-system-resolved");
    expect(res.sessionState.intent?.slots?.SystemName?.value?.interpretedValue).toBe("VPN");
  });
  test("multiple resolved values: ask which one, naming both", async () => {
    const { res } = await run("reset-system-ambiguous");
    assertValidResponse(res);
    expect(res.sessionState.dialogAction).toMatchObject({ type: "ElicitSlot", slotToElicit: "SystemName" });
    expect(said(res)).toMatch(/SAP/);
    expect(said(res)).toMatch(/Concur/);
    expect(res.sessionState.intent?.slots?.SystemName ?? null).toBeNull();
  });
  test("no resolved value: re-elicit listing the supported systems", async () => {
    const { res } = await run("reset-system-unresolved");
    expect(res.sessionState.dialogAction).toMatchObject({ type: "ElicitSlot", slotToElicit: "SystemName" });
    expect(said(res)).toMatch(/Workday/);
  });
});

describe("confirmation", () => {
  test("confirmation message does not read back the full employee id", async () => {
    const { res } = await run("reset-system-resolved");
    expect(said(res)).not.toMatch(/44129/);
  });
  test("Confirmed delegates to Lex (which then runs fulfillment)", async () => {
    const { res, calls } = await run("reset-confirmed");
    assertValidResponse(res);
    expect(res.sessionState.dialogAction.type).toBe("Delegate");
    expect(calls.reset).toEqual([]);
  });
  test("Denied asks for the system again instead of resetting", async () => {
    const { res, calls } = await run("reset-denied");
    assertValidResponse(res);
    expect(res.sessionState.dialogAction).toMatchObject({ type: "ElicitSlot", slotToElicit: "SystemName" });
    expect(calls.reset).toEqual([]);
  });
  test("the dialog hook never calls the reset service", async () => {
    for (const f of ["reset-employee-id-valid", "reset-system-resolved", "reset-confirmed"]) {
      const { calls } = await run(f);
      expect(calls.reset).toEqual([]);
    }
  });
});

describe("fulfillment and handoff contract", () => {
  test("NO_MFA hands off to PasswordReset with a summary and the slots", async () => {
    const { res } = await run("reset-fulfill-no-mfa");
    assertValidResponse(res);
    const a = attrsOf(res);
    expect(res.sessionState.intent?.state).toBe("Failed");
    expect(a).toMatchObject({ handoff: "true", handoffReason: "NO_MFA", handoffQueue: "PasswordReset", intent: "ResetPassword" });
    expect(JSON.parse(a.slots)).toMatchObject({ EmployeeId: "30077", SystemName: "EMAIL" });
    expect(a.summary.length).toBeGreaterThan(10);
    expect(a.summary.length).toBeLessThanOrEqual(300);
  });
  test("reset service FAILED hands off with RESET_FAILED", async () => {
    const { res } = await run("reset-fulfill", { resetResult: "FAILED" });
    expect(attrsOf(res)).toMatchObject({ handoff: "true", handoffReason: "RESET_FAILED", handoffQueue: "PasswordReset" });
  });
  test("a backend exception never escapes: Close + BACKEND_ERROR handoff", async () => {
    const { res } = await run("reset-fulfill", { throwOn: "reset" });
    assertValidResponse(res);
    expect(attrsOf(res)).toMatchObject({ handoff: "true", handoffReason: "BACKEND_ERROR" });
  });
  test("directory failure during the dialog also hands off cleanly", async () => {
    const { res } = await run("reset-employee-id-valid", { throwOn: "lookup" });
    assertValidResponse(res);
    expect(attrsOf(res).handoffReason).toBe("BACKEND_ERROR");
  });
  test("chat fulfillment returns PlainText and keeps the chat attributes", async () => {
    const { res } = await run("reset-fulfill-chat");
    assertValidResponse(res);
    expect(res.messages?.[0].contentType).toBe("PlainText");
    expect(attrsOf(res).channel).toBe("CHAT");
    expect(said(res)).toMatch(/Workday/);
  });
  test("successful self-service does not flag a handoff", async () => {
    const { res } = await run("reset-fulfill");
    expect(attrsOf(res).handoff === undefined || attrsOf(res).handoff === "false").toBe(true);
  });
  test("incoming attributes survive a handoff", async () => {
    const { res } = await run("reset-fulfill-no-mfa");
    expect(attrsOf(res)).toMatchObject({ contactId: "4a573372-1f28-4e26-b97b-6c1d2e3f4a5b", callerVerified: "false" });
  });
});

describe("other intents", () => {
  test("UnlockAccount dialog asks for the employee id", async () => {
    const { res } = await run("unlock-initial");
    expect(res.sessionState.dialogAction).toMatchObject({ type: "ElicitSlot", slotToElicit: "EmployeeId" });
  });
  test("UnlockAccount on a locked account unlocks and closes Fulfilled", async () => {
    const { res, calls } = await run("unlock-fulfill-locked");
    assertValidResponse(res);
    expect(calls.unlock).toEqual(["44129"]);
    expect(res.sessionState.intent?.state).toBe("Fulfilled");
  });
  test("UnlockAccount on a disabled account never unlocks and goes to Security", async () => {
    const { res, calls } = await run("unlock-fulfill-disabled");
    expect(calls.unlock).toEqual([]);
    expect(attrsOf(res)).toMatchObject({ handoff: "true", handoffReason: "ACCOUNT_DISABLED", handoffQueue: "Security" });
  });
  test("ReportOutage affecting many people goes to MajorIncident", async () => {
    const { res } = await run("outage-many");
    assertValidResponse(res);
    expect(attrsOf(res)).toMatchObject({ handoff: "true", handoffReason: "OUTAGE_REPORTED", handoffQueue: "MajorIncident" });
  });
  test("ReportOutage for one person goes to GeneralSupport", async () => {
    const { res } = await run("outage-just-me");
    expect(attrsOf(res).handoffQueue).toBe("GeneralSupport");
  });
  test("first fallback re-prompts with ElicitIntent and counts it", async () => {
    const { res } = await run("fallback-first");
    assertValidResponse(res);
    expect(res.sessionState.dialogAction.type).toBe("ElicitIntent");
    expect(attrsOf(res).fallbackCount).toBe("1");
  });
  test("second fallback hands off with the last utterance in the summary", async () => {
    const { res } = await run("fallback-second");
    assertValidResponse(res);
    expect(attrsOf(res)).toMatchObject({ handoff: "true", handoffReason: "NOT_UNDERSTOOD" });
    expect(attrsOf(res).summary).toMatch(/screen/);
  });
  test("an intent the Lambda does not know hands off instead of throwing", async () => {
    const ev = fixture("reset-fulfill");
    ev.sessionState.intent.name = "OrderLaptop";
    const res = await createHandler(makeDeps().deps)(ev);
    assertValidResponse(res);
    expect(attrsOf(res).handoff).toBe("true");
  });
});
