// Hidden tests for connect/w3-c1 (run from tests/__hidden__).
import * as fs from "fs";
import * as path from "path";
import { handler } from "../../src/handler";
import { runCall, newInboundEvent, contractErrors } from "../sma-sim";

const fx = (n: string) => JSON.parse(fs.readFileSync(path.join(__dirname, "../../fixtures", n), "utf8"));
let logs: string[] = [];
beforeEach(() => { logs = []; jest.spyOn(console, "log").mockImplementation((...a: any[]) => { logs.push(a.join(" ")); }); });
afterEach(() => jest.restoreAllMocks());

test("primary does not answer: the secondary is tried next", async () => {
  const r = await runCall(handler, { digits: ["104233", "1"], bridges: ["noanswer", "answer"] });
  expect(r.errors).toEqual([]);
  expect(r.bridged).toEqual(["+16465550171", "+12125550161"]);
});

test("neither engineer answers: caller hears the unavailable prompt and goes to the help desk", async () => {
  const r = await runCall(handler, { digits: ["104233", "1"], bridges: ["noanswer", "noanswer", "answer"] });
  expect(r.errors).toEqual([]);
  expect(r.bridged).toEqual(["+16465550171", "+12125550161", "+18005550142"]);
  expect(r.played).toContain("oncall-unavailable.wav");
});

test("on-call engineer is resolved from the call start time, not the Lambda clock", async () => {
  const saturdayNoon = Date.UTC(2026, 9, 10, 16, 0, 0); // Sat 12:00 New York -> weekend shift
  const r = await runCall(handler, { digits: ["104233", "1"], startTimeMs: saturdayNoon });
  expect(r.bridged[0]).toBe("+19175550188");
});

test("no valid employee id after the retries: goodbye and hang up", async () => {
  const r = await runCall(handler, { digits: [null] });
  expect(r.errors).toEqual([]);
  expect(r.played).toContain("goodbye.wav");
  expect(r.ended).toBe(true);
});

test("caller hangs up while bridged: the engineer leg is hung up too", async () => {
  const r = await runCall(handler, { digits: ["104233", "1"], hangupAfterBridge: "LEG-A" });
  expect(r.errors).toEqual([]);
  const last = r.steps[r.steps.length - 1];
  expect(last.event.InvocationEventType).toBe("HANGUP");
  expect(last.response.Actions.map((a) => a.Type)).toEqual(["Hangup"]);
  expect(last.response.Actions[0].Parameters.ParticipantTag).toBe("LEG-B");
  expect(r.ended).toBe(true);
});

test("engineer hangs up first: caller hears a message and is hung up", async () => {
  const r = await runCall(handler, { digits: ["104233", "1"], hangupAfterBridge: "LEG-B" });
  expect(r.errors).toEqual([]);
  expect(r.played).toContain("engineer-disconnected.wav");
  expect(r.ended).toBe(true);
});

test("recorded HANGUP fixture (caller left a bridged call) hangs up LEG-B by CallId", async () => {
  const out = await handler(fx("hangup-leg-a-while-bridged.json"));
  expect(out.Actions).toHaveLength(1);
  expect(out.Actions[0].Type).toBe("Hangup");
  expect(out.Actions[0].Parameters.CallId).toBe("e8a1b6c4-2f0d-4e3b-a9c7-5d4e3f2a1b00");
});

test("recorded ACTION_FAILED fixture (primary no answer) bridges the secondary from TransactionAttributes", async () => {
  const out = await handler(fx("action-failed-bridge-primary.json"));
  const b = out.Actions.find((a) => a.Type === "CallAndBridge")!;
  expect(b.Parameters.Endpoints[0].Uri).toBe("+12125550161");
});

test("two concurrent calls in one warm container do not share state", async () => {
  const e1 = newInboundEvent({ transactionId: "tx-A" });
  const e2 = newInboundEvent({ transactionId: "tx-B" });
  const r1 = await handler(e1);
  const r2 = await handler(e2);
  // call A enters its id and gets the menu; call B is still at the id prompt
  const a2 = await handler({ ...e1, Sequence: 2, InvocationEventType: "ACTION_SUCCESSFUL", ActionData: { Type: "PlayAudioAndGetDigits", Parameters: r1.Actions[0].Parameters, ReceivedDigits: "111111" }, CallDetails: { ...e1.CallDetails, TransactionAttributes: r1.TransactionAttributes } });
  // call B now presses digits for its id prompt
  const b2 = await handler({ ...e2, Sequence: 2, InvocationEventType: "ACTION_SUCCESSFUL", ActionData: { Type: "PlayAudioAndGetDigits", Parameters: r2.Actions[0].Parameters, ReceivedDigits: "222222" }, CallDetails: { ...e2.CallDetails, TransactionAttributes: r2.TransactionAttributes } });
  expect(a2.TransactionAttributes?.employeeId).toBe("111111");
  expect(b2.TransactionAttributes?.employeeId).toBe("222222");
  expect(b2.Actions[0].Parameters.InputDigitsRegex).toBe("^[12]$");
});

test("a retried invocation (same event twice) produces the same response", async () => {
  const e = newInboundEvent({ transactionId: "tx-R" });
  const r1 = await handler(JSON.parse(JSON.stringify(e)));
  const step2 = { ...e, Sequence: 2, InvocationEventType: "ACTION_SUCCESSFUL" as const, ActionData: { Type: "PlayAudioAndGetDigits", Parameters: r1.Actions[0].Parameters, ReceivedDigits: "333333" }, CallDetails: { ...e.CallDetails, TransactionAttributes: r1.TransactionAttributes } };
  const x = await handler(JSON.parse(JSON.stringify(step2)));
  const y = await handler(JSON.parse(JSON.stringify(step2)));
  expect(y).toEqual(x);
});

test("an invalid X-Employee-Id header is ignored and the caller is asked for the id", async () => {
  const out = await handler(newInboundEvent({ sipHeaders: { "X-Employee-Id": "abc'; DROP" } }));
  expect(out.Actions[0].Parameters.InputDigitsRegex).toBe("^\\d{6}$");
});

test("INVALID_LAMBDA_RESPONSE hangs up the caller cleanly", async () => {
  const e = newInboundEvent();
  const out = await handler({ ...e, Sequence: 3, InvocationEventType: "INVALID_LAMBDA_RESPONSE", ActionData: { Type: "PlayAudio", Parameters: {}, ErrorType: "InvalidResponse", ErrorMessage: "bad" } });
  expect(out.Actions.map((a) => a.Type)).toEqual(["Hangup"]);
});

test("unknown or unhandled event types never throw and return a valid empty action list", async () => {
  const e = newInboundEvent();
  const out = await handler({ ...e, Sequence: 9, InvocationEventType: "CALL_UPDATE_REQUESTED" });
  expect(contractErrors(out, e.CallDetails.Participants)).toEqual([]);
  expect(out.Actions).toEqual([]);
});

test("every TransactionAttributes value is a string and the full employee id never reaches the logs", async () => {
  const r = await runCall(handler, { digits: ["104233", "1"], hangupAfterBridge: "LEG-A" });
  for (const s of r.steps) for (const v of Object.values(s.response.TransactionAttributes || {})) expect(typeof v).toBe("string");
  expect(logs.join("\n")).not.toContain("104233");
  expect(logs.length).toBeGreaterThan(0);
});
