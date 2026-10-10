// Visible tests for connect/ai-t1. Budgets are scaled down (1200 ms instead of 6500 ms) so the suite is fast.
import { buildHandler } from "../src/handler";
import { makeClient } from "../src/client";
import { FakeBedrockHttp, event, ctx } from "./fakeBedrock";

const quiet = () => undefined;

test("healthy Bedrock: OK summary as a flat string map", async () => {
  const http = new FakeBedrockHttp([{ status: 200, delayMs: 150 }]);
  const handler = buildHandler({ client: makeClient(http), flowBudgetMs: 1200, log: quiet });
  const r = await handler(event(), ctx());
  expect(r.summaryStatus).toBe("OK");
  expect(r.summary).toMatch(/MFA/);
  for (const v of Object.values(r)) expect(typeof v).toBe("string");
});

test("a slow model answer returns DEGRADED inside the budget instead of letting Connect time out", async () => {
  const http = new FakeBedrockHttp([{ status: 200, delayMs: 3000 }]);
  const handler = buildHandler({ client: makeClient(http), flowBudgetMs: 1200, log: quiet });
  const t0 = Date.now();
  const r = await handler(event(), ctx());
  expect(Date.now() - t0).toBeLessThan(1300);
  expect(r.summaryStatus).toBe("DEGRADED");
}, 10000);
