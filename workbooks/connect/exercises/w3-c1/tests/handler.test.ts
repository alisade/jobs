// Visible tests for connect/w3-c1. The grader adds more (failover, hangups, concurrency, replay).
import * as fs from "fs";
import * as path from "path";
import { handler } from "../src/handler";
import { runCall, HOTLINE } from "./sma-sim";

const quiet = () => jest.spyOn(console, "log").mockImplementation(() => undefined);
beforeEach(() => { quiet(); });
afterEach(() => jest.restoreAllMocks());

test("a new call asks for the six-digit employee id", async () => {
  const r = await runCall(handler, { digits: [] });
  expect(r.errors).toEqual([]);
  const first = r.steps[0].response.Actions[0];
  expect(first.Type).toBe("PlayAudioAndGetDigits");
  expect(first.Parameters.InputDigitsRegex).toBe("^\\d{6}$");
});

test("valid id then 2 bridges the caller to the Connect help desk number", async () => {
  const r = await runCall(handler, { digits: ["104233", "2"] });
  expect(r.errors).toEqual([]);
  expect(r.bridged).toEqual(["+18005550142"]);
});

test("valid id then 1 bridges to the on-call primary and presents the hotline number", async () => {
  const r = await runCall(handler, { digits: ["104233", "1"] });
  expect(r.errors).toEqual([]);
  expect(r.bridged).toEqual(["+16465550171"]); // Tue 22:14 New York = evening shift
  const bridge = r.steps.flatMap((s) => s.response.Actions).find((a) => a.Type === "CallAndBridge")!;
  expect(bridge.Parameters.CallerIdNumber).toBe(HOTLINE);
});

test("an employee id passed by the Avaya SBC in X-Employee-Id skips the id prompt", async () => {
  const ev = JSON.parse(fs.readFileSync(path.join(__dirname, "../fixtures/new-inbound-call-from-avaya.json"), "utf8"));
  const out = await handler(ev);
  expect(out.Actions[0].Parameters.InputDigitsRegex).toBe("^[12]$");
  expect(out.TransactionAttributes?.employeeId).toBe("104233");
});
