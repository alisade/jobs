// Hidden tests for backend/w4-c1 (run from tests/__hidden__/).
import { EventEmitter } from "events";
import { start, stop, transition, rows, Ctx } from "../helpers";
import { installGracefulShutdown } from "../../src/shutdown";

let ctx: Ctx | undefined;
afterEach(async () => { await stop(ctx); ctx = undefined; });

const problemOf = (res: { statusCode: number; headers: Record<string, unknown>; json: () => any }) => {
  expect(String(res.headers["content-type"])).toMatch(/application\/problem\+json/);
  const p = res.json();
  expect(p.status).toBe(res.statusCode);
  expect(typeof p.type).toBe("string");
  expect(typeof p.title).toBe("string");
  return p;
};

test("body validation: unknown stage, non-integer version and junk fields are 400 problems with errors", async () => {
  ctx = await start();
  for (const body of [{ to_stage: "won_maybe", expected_version: 1 }, { to_stage: "qualification", expected_version: "1" },
    { to_stage: "qualification" }, { to_stage: "qualification", expected_version: 1.5 }]) {
    const res = await transition(ctx, 1, body);
    expect(res.statusCode).toBe(400);
    const p = problemOf(res);
    expect(Array.isArray(p.errors)).toBe(true);
  }
  expect(await rows(ctx, "SELECT * FROM outbox")).toHaveLength(0);
});

test("malformed JSON is a 400 problem, not a 500", async () => {
  ctx = await start();
  const res = await ctx.app.inject({ method: "POST", url: "/v1/opportunities/1/transitions",
    headers: { "content-type": "application/json", "x-tenant-id": "bu-emea" }, payload: "{not json" });
  expect(res.statusCode).toBe(400);
  problemOf(res);
});

test("another tenant's opportunity is a 404 (RLS), and nothing is written", async () => {
  ctx = await start();
  const res = await transition(ctx, 4, { to_stage: "proposal", expected_version: 1 }, "bu-emea");
  expect(res.statusCode).toBe(404);
  problemOf(res);
  expect(await rows(ctx, "SELECT stage FROM opportunities WHERE id = 4")).toEqual([{ stage: "qualification" }]);
  expect(await rows(ctx, "SELECT * FROM outbox")).toHaveLength(0);
});

test("an unknown id is a 404 problem", async () => {
  ctx = await start();
  const res = await transition(ctx, 9999, { to_stage: "proposal", expected_version: 1 });
  expect(res.statusCode).toBe(404);
  problemOf(res);
});

test("closed_won needs amount > 0 and a close_date", async () => {
  ctx = await start();
  const noAmount = await transition(ctx, 3, { to_stage: "closed_won", expected_version: 1, close_date: "2026-11-30" });
  expect(noAmount.statusCode).toBe(422);
  problemOf(noAmount);
  const noDate = await transition(ctx, 2, { to_stage: "closed_won", expected_version: 3 });
  expect(noDate.statusCode).toBe(422);
  const ok = await transition(ctx, 2, { to_stage: "closed_won", expected_version: 3, close_date: "2026-11-30" });
  expect(ok.statusCode).toBe(200);
  const r = await rows<{ stage: string; close_date: Date; version: number }>(ctx, "SELECT stage, close_date::text AS close_date, version FROM opportunities WHERE id = 2");
  expect(r[0]).toEqual({ stage: "closed_won", close_date: "2026-11-30", version: 4 });
});

test("closed stages are terminal", async () => {
  ctx = await start();
  const res = await transition(ctx, 5, { to_stage: "prospecting", expected_version: 2 });
  expect(res.statusCode).toBe(422);
  problemOf(res);
});

test("a failure after the writes rolls everything back: no outbox, no history, version unchanged", async () => {
  ctx = await start({ beforeCommit: async () => { throw new Error("simulated crash before commit"); } });
  const res = await transition(ctx, 6, { to_stage: "negotiation", expected_version: 1 });
  expect(res.statusCode).toBe(500);
  const p = problemOf(res);
  expect(JSON.stringify(p)).not.toMatch(/simulated crash/);
  expect(await rows(ctx, "SELECT stage, version FROM opportunities WHERE id = 6")).toEqual([{ stage: "proposal", version: 1 }]);
  expect(await rows(ctx, "SELECT * FROM outbox")).toHaveLength(0);
  expect(await rows(ctx, "SELECT * FROM stage_history")).toHaveLength(0);
});

test("two concurrent transitions with the same expected_version: one 200, one 409, one outbox row", async () => {
  ctx = await start({ afterLock: () => new Promise((r) => setTimeout(r, 30)) });
  const [a, b] = await Promise.all([
    transition(ctx, 6, { to_stage: "negotiation", expected_version: 1 }),
    transition(ctx, 6, { to_stage: "qualification", expected_version: 1 }),
  ]);
  expect([a.statusCode, b.statusCode].sort()).toEqual([200, 409]);
  expect(await rows(ctx, "SELECT * FROM outbox")).toHaveLength(1);
  expect(await rows(ctx, "SELECT version FROM opportunities WHERE id = 6")).toEqual([{ version: 2 }]);
});

test("the opportunity row is locked with SELECT ... FOR UPDATE inside the transaction", async () => {
  ctx = await start();
  const res = await transition(ctx, 1, { to_stage: "qualification", expected_version: 1 });
  expect(res.statusCode).toBe(200);
  expect(ctx.sqlLog.some((q) => /select[\s\S]*from "?opportunities"?[\s\S]*for update/i.test(q))).toBe(true);
});

test("the tenant setting does not leak past the transaction", async () => {
  ctx = await start();
  await transition(ctx, 1, { to_stage: "qualification", expected_version: 1 });
  const r = await rows<{ t: string | null; u: string }>(ctx, "SELECT current_setting('app.tenant_id', true) AS t, current_user AS u");
  expect(r[0].t === null || r[0].t === "").toBe(true);
  expect(r[0].u).toBe("postgres");
});

test("outbox payload carries the event id, from/to stage, version and account", async () => {
  ctx = await start();
  const res = await transition(ctx, 6, { to_stage: "negotiation", expected_version: 1 });
  const ob = await rows<{ payload: Record<string, unknown>; tenant_id: string; published_at: unknown }>(
    ctx, "SELECT payload, tenant_id, published_at FROM outbox");
  expect(ob[0]).toMatchObject({ tenant_id: "bu-emea", published_at: null });
  expect(ob[0].payload).toMatchObject({ event_id: res.json().event_id, opportunity_id: 6, account_id: 104,
    from_stage: "proposal", to_stage: "negotiation", version: 2 });
});

test("graceful shutdown: readyz goes 503, new requests get 503 problems, in-flight finishes, then exit(0)", async () => {
  let release!: () => void;
  const gate = new Promise<void>((r) => { release = r; });
  let entered!: () => void;
  const inside = new Promise<void>((r) => { entered = r; });
  const signals = new EventEmitter();
  const exits: number[] = [];
  ctx = await start({ afterLock: async () => { entered(); await gate; } },
    (app) => installGracefulShutdown(app, { signals, exit: (c) => exits.push(c), timeoutMs: 5000 }));

  const inflight = transition(ctx, 6, { to_stage: "negotiation", expected_version: 1 });
  await Promise.race([inside, new Promise((_, rej) => setTimeout(() => rej(new Error("request never reached the lock")), 5000))]);
  signals.emit("SIGTERM");
  await new Promise((r) => setTimeout(r, 30));
  expect(exits).toEqual([]);
  const ready = await ctx.app.inject({ method: "GET", url: "/readyz" });
  expect(ready.statusCode).toBe(503);
  const fresh = await ctx.app.inject({ method: "GET", url: "/v1/opportunities/1", headers: { "x-tenant-id": "bu-emea" } });
  expect(fresh.statusCode).toBe(503);
  problemOf(fresh);

  release();
  const done = await inflight;
  expect(done.statusCode).toBe(200);
  const t0 = Date.now();
  while (exits.length === 0 && Date.now() - t0 < 3000) await new Promise((r) => setTimeout(r, 10));
  expect(exits).toEqual([0]);
});
