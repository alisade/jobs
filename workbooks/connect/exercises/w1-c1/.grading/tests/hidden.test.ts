// Hidden tests for connect/w1-c1 (copied to tests/__hidden__ by the grader).
import { validateFlow, edges, reachable } from "connect-kit";
import { loadFlow, run, res } from "../harness";

const flow = loadFlow();
const byType = (t: string) => flow.Actions.filter((a) => a.Type === t);

describe("graph rules", () => {
  test("no unbounded loops", () => {
    expect(validateFlow(flow).issues.filter((i) => i.code === "UNBOUNDED_LOOP")).toEqual([]);
  });
  test("no attribute or Lambda result used before it is set", () => {
    expect(validateFlow(flow).issues.filter((i) => i.code === "ATTR_BEFORE_SET")).toEqual([]);
  });
  test("every Lambda invoke is synchronous with a time limit inside Connect's 8 s and handles errors", () => {
    const l = byType("InvokeLambdaFunction");
    expect(l.length).toBeGreaterThanOrEqual(2);
    for (const a of l) {
      expect(Number(a.Parameters.InvocationTimeLimitSeconds)).toBeLessThanOrEqual(8);
      expect((a.Transitions.Errors || []).map((e) => e.ErrorType)).toContain("NoMatchingError");
    }
  });
  test("caller identification gets a tight budget (<= 3 s) so a slow directory never stalls the IVR", () => {
    const a = byType("InvokeLambdaFunction").find((x) => x.Parameters.LambdaFunctionARN === res.lambdas.identifyCaller)!;
    expect(Number(a.Parameters.InvocationTimeLimitSeconds)).toBeLessThanOrEqual(3);
  });
  test("flow logging is enabled before anything else", () => {
    const start = flow.Actions.find((a) => a.Identifier === flow.StartAction)!;
    expect(start.Type).toBe("UpdateFlowLoggingBehavior");
    expect(start.Parameters.FlowLoggingBehavior).toBe("Enabled");
  });
  test("every reachable non-terminal action has somewhere to go", () => {
    expect(validateFlow(flow).issues.filter((i) => i.code === "DEAD_END" || i.code === "MISSING_ERROR_BRANCH")).toEqual([]);
  });
  test("no prompt reads back employee identifiers", () => {
    const texts = flow.Actions.map((a) => String(a.Parameters.Text || a.Parameters.SSML || ""));
    expect(texts.filter((t) => /\$\.(Attributes|External)\.employeeId/.test(t))).toEqual([]);
  });
  test("every reachable path terminates (all actions reachable or flagged)", () => {
    const r = reachable(flow);
    for (const id of r) {
      const a = flow.Actions.find((x) => x.Identifier === id)!;
      for (const e of edges(a)) expect(flow.Actions.some((x) => x.Identifier === e.to)).toBe(true);
    }
  });
});

describe("call paths", () => {
  test("menu: two misses then a valid key still routes (3 attempts in total)", () => {
    const r = run({ inputs: [null, "7", "2"] });
    expect(r.outcome).toBe("TransferredToQueue");
    expect(r.queueName).toBe("GeneralSupport");
  });
  test("menu: three misses fall through to GeneralSupport instead of dropping the caller", () => {
    const r = run({ inputs: [null, null, null, null, null] });
    expect(r.outcome).toBe("TransferredToQueue");
    expect(r.queueName).toBe("GeneralSupport");
    expect(r.prompts.filter((p) => /password resets, press 1/i.test(p)).length).toBe(3);
  });
  test("option 3 reports an outage to MajorIncident at priority 1", () => {
    const r = run({ inputs: ["3"] });
    expect(r.queueName).toBe("MajorIncident");
    expect(r.routing.priority).toBe(1);
  });
  test("VIP callers skip the menu and go to VIPDesk at priority 1", () => {
    const r = run({ vip: true });
    expect(r.outcome).toBe("TransferredToQueue");
    expect(r.queueName).toBe("VIPDesk");
    expect(r.routing.priority).toBe(1);
    expect(r.prompts.some((p) => /press 1/i.test(p))).toBe(false);
  });
  test("identify Lambda error: caller is marked unverified and still gets the menu", () => {
    const r = run({ identify: "error", inputs: ["2"] });
    expect(r.attributes.callerVerified).toBe("false");
    expect(r.queueName).toBe("GeneralSupport");
  });
  test("identify Lambda slower than its time limit takes the error branch", () => {
    const r = run({ identify: "slow", inputs: ["2"] });
    expect(r.attributes.callerVerified).toBe("false");
    expect(r.outcome).toBe("TransferredToQueue");
  });
  test("successful identification copies the Lambda result into contact attributes", () => {
    const r = run({ inputs: ["2"] });
    expect(r.attributes.employeeId).toBe("E10442");
    expect(r.attributes.callerVerified).toBe("true");
  });
  test("password reset reported FAILED goes to the PasswordReset queue", () => {
    const r = run({ inputs: ["1"], reset: "FAILED" });
    expect(r.queueName).toBe("PasswordReset");
  });
  test("password reset Lambda error goes to the PasswordReset queue", () => {
    const r = run({ inputs: ["1"], reset: "error" });
    expect(r.queueName).toBe("PasswordReset");
  });
  test("password reset passes the employee id to the Lambda", () => {
    const r = run({ inputs: ["1"] });
    const call = r.lambdaCalls.find((c) => c.arn === res.lambdas.passwordReset)!;
    expect(call.payload.Details.Parameters.employeeId).toBe("E10442");
  });
  test("no staffed agents on the target queue overflows to GeneralSupport with a message", () => {
    const r = run({ inputs: ["1"], reset: "FAILED", staffed: { PasswordReset: 0 } });
    expect(r.queueName).toBe("GeneralSupport");
    expect(r.outcome).toBe("TransferredToQueue");
    expect(r.prompts.join(" ")).toMatch(/busy|general/i);
  });
  test("queue at capacity plays a message and disconnects (never a silent drop)", () => {
    const r = run({ inputs: ["2"], atCapacity: ["GeneralSupport"] });
    expect(r.outcome).toBe("Disconnected");
    expect(r.prompts[r.prompts.length - 1]).toMatch(/high number of calls|try again later|portal/i);
  });
  test("after hours: pressing 9 reports an outage to the 24x7 MajorIncident queue", () => {
    const r = run({ open: false, inputs: ["9"] });
    expect(r.queueName).toBe("MajorIncident");
    expect(r.outcome).toBe("TransferredToQueue");
  });
  test("after hours: the message points callers at the self-service portal", () => {
    const r = run({ open: false, inputs: [null] });
    expect(r.prompts.join(" ")).toMatch(/portal/i);
  });
});
