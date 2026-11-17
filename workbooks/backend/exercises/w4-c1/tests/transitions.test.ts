// Visible tests for backend/w4-c1. The grader adds hidden tests for the rest of the README.
import { start, stop, transition, rows, Ctx } from "./helpers";

let ctx: Ctx;
beforeEach(async () => { ctx = await start(); });
afterEach(async () => { await stop(ctx); });

test("happy path: stage moves, version bumps, history and outbox rows are written", async () => {
  const res = await transition(ctx, 1, { to_stage: "qualification", expected_version: 1 });
  expect(res.statusCode).toBe(200);
  const body = res.json();
  expect(body).toMatchObject({ id: 1, stage: "qualification", version: 2 });
  const opp = await rows<{ stage: string; version: number }>(ctx, "SELECT stage, version FROM opportunities WHERE id = 1");
  expect(opp[0]).toEqual({ stage: "qualification", version: 2 });
  expect(await rows(ctx, "SELECT from_stage, to_stage, version FROM stage_history WHERE opportunity_id = 1"))
    .toEqual([{ from_stage: "prospecting", to_stage: "qualification", version: 2 }]);
  const ob = await rows<{ event_id: string; type: string; aggregate_id: string; payload: Record<string, unknown> }>(
    ctx, "SELECT event_id::text AS event_id, type, aggregate_id, payload FROM outbox");
  expect(ob).toHaveLength(1);
  expect(ob[0]).toMatchObject({ event_id: body.event_id, type: "OpportunityStageChanged", aggregate_id: "1" });
  expect(ob[0].payload).toMatchObject({ from_stage: "prospecting", to_stage: "qualification", version: 2 });
});

test("missing X-Tenant-Id is a 400 problem+json", async () => {
  const res = await transition(ctx, 1, { to_stage: "qualification", expected_version: 1 }, null);
  expect(res.statusCode).toBe(400);
  expect(res.headers["content-type"]).toMatch(/application\/problem\+json/);
  expect(res.json()).toMatchObject({ status: 400, title: expect.any(String), type: expect.stringMatching(/^https?:\/\//) });
});

test("an illegal transition is a 422 and changes nothing", async () => {
  const res = await transition(ctx, 1, { to_stage: "closed_won", expected_version: 1 });
  expect(res.statusCode).toBe(422);
  expect(res.headers["content-type"]).toMatch(/application\/problem\+json/);
  expect(await rows(ctx, "SELECT stage, version FROM opportunities WHERE id = 1")).toEqual([{ stage: "prospecting", version: 1 }]);
  expect(await rows(ctx, "SELECT * FROM outbox")).toHaveLength(0);
});

test("a stale expected_version is a 409", async () => {
  const res = await transition(ctx, 6, { to_stage: "negotiation", expected_version: 7 });
  expect(res.statusCode).toBe(409);
  expect(res.json()).toMatchObject({ status: 409, current_version: 1 });
});
