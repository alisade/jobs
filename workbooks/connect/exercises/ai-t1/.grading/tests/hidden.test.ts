// Hidden tests for connect/ai-t1.
import * as fs from "fs";
import * as path from "path";
import { buildHandler } from "../../src/handler";
import { makeClient } from "../../src/client";
import { FakeBedrockHttp, event, ctx } from "../fakeBedrock";

const quiet = () => undefined;
const root = path.resolve(__dirname, "../..");
const BUDGET = 1200;

async function timed(steps: any[], opts: { budget?: number; remaining?: number } = {}) {
  const http = new FakeBedrockHttp(steps);
  const handler = buildHandler({ client: makeClient(http), flowBudgetMs: opts.budget || BUDGET, log: quiet });
  const t0 = Date.now();
  let r: any;
  let threw: any = null;
  try { r = await handler(event(), ctx(opts.remaining || 8000)); } catch (e) { threw = e; }
  return { r, threw, ms: Date.now() - t0, http };
}

test("throttling storm: never throws, DEGRADED/throttled or timeout inside the budget", async () => {
  const { r, threw, ms } = await timed([{ status: 429, delayMs: 200 }]);
  expect(threw).toBeNull();
  expect(ms).toBeLessThan(BUDGET + 100);
  expect(r.summaryStatus).toBe("DEGRADED");
  expect(["throttled", "timeout"]).toContain(r.degradedReason);
}, 15000);

test("one throttle then a fast success still produces a summary when it fits the budget", async () => {
  const { r, ms } = await timed([{ status: 429, delayMs: 50 }, { status: 200, delayMs: 100 }], { budget: 3000 });
  expect(r.summaryStatus).toBe("OK");
  expect(ms).toBeLessThan(3000);
}, 15000);

test("throttle then a slow success: DEGRADED inside the budget (no unbounded retry chain)", async () => {
  const { r, ms } = await timed([{ status: 429, delayMs: 200 }, { status: 200, delayMs: 2500 }]);
  expect(ms).toBeLessThan(BUDGET + 100);
  expect(r.summaryStatus).toBe("DEGRADED");
}, 15000);

test("a 500 from Bedrock degrades with reason error, never an exception", async () => {
  const { r, threw, ms } = await timed([{ status: 500, delayMs: 50 }], { budget: 4000 });
  expect(threw).toBeNull();
  expect(r.summaryStatus).toBe("DEGRADED");
  expect(ms).toBeLessThan(4000);
}, 15000);

test("the deadline also respects the Lambda's own remaining time", async () => {
  const { r, ms } = await timed([{ status: 200, delayMs: 3000 }], { budget: 6500, remaining: 900 });
  expect(ms).toBeLessThan(900);
  expect(r.summaryStatus).toBe("DEGRADED");
}, 15000);

test("a scaled throttle storm with the production budget ratio finishes far below Connect's 8 s", async () => {
  const { r, threw, ms } = await timed([{ status: 429, delayMs: 300 }], { budget: 2000 });
  expect(threw).toBeNull();
  expect(r.summaryStatus).toBe("DEGRADED");
  expect(ms).toBeLessThan(2100);
}, 15000);

test("the request asks for a short summary: maxTokens <= 400", async () => {
  const { http } = await timed([{ status: 200, delayMs: 20 }]);
  expect(http.requests[0].body.inferenceConfig.maxTokens).toBeLessThanOrEqual(400);
});

test("a degraded result is still a flat string map with all three keys", async () => {
  const { r } = await timed([{ status: 200, delayMs: 3000 }]);
  expect(Object.keys(r).sort()).toEqual(["degradedReason", "summary", "summaryStatus"]);
  for (const v of Object.values(r)) expect(typeof v).toBe("string");
}, 10000);

test("Lambda timeout is no longer than Connect's synchronous limit (8 s): no orphaned 30 s invocations", () => {
  const cfg = JSON.parse(fs.readFileSync(path.join(root, "config/lambda.json"), "utf8"));
  expect(cfg.Timeout).toBeLessThanOrEqual(8);
  expect(Number(cfg.Environment.Variables.MAX_TOKENS)).toBeLessThanOrEqual(400);
});

test("an empty transcript degrades immediately without calling Bedrock", async () => {
  const http = new FakeBedrockHttp([{ status: 200, delayMs: 50 }]);
  const handler = buildHandler({ client: makeClient(http), flowBudgetMs: BUDGET, log: quiet });
  const r = await handler(event(""), ctx());
  expect(r.summaryStatus).toBe("DEGRADED");
  expect(http.requests).toHaveLength(0);
});
