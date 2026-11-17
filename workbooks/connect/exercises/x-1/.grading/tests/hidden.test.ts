// Hidden tests for connect/x-1 (copied to tests/__hidden__ by the grader).
import { mockClient } from "aws-sdk-client-mock";
import { DynamoDBDocumentClient, PutCommand } from "@aws-sdk/lib-dynamodb";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { createHandler } from "../../src/handler";
import { DynamoIdempotencyStore, InMemoryIdempotencyStore } from "../../src/idempotency";
import { event, fakeSn, fastSleep, incidents } from "../harness";

const withSn = async (faults: any, fn: (x: Awaited<ReturnType<typeof fakeSn>>) => Promise<void>) => {
  const x = await fakeSn(faults);
  try {
    await fn(x);
  } finally {
    await x.sn.stop();
  }
};

describe("ambiguous create failures", () => {
  test("gateway timeout AFTER ServiceNow committed: still exactly one incident, and its number is returned", () =>
    withSn({ createCommitThenFail: [1] }, async ({ sn, client }) => {
      const out = await createHandler({ sn: client, store: new InMemoryIdempotencyStore(), sleep: fastSleep })(event("c-1001"));
      const rows = incidents(sn, "c-1001");
      expect(rows).toHaveLength(1);
      expect(out.incidentNumber).toBe(rows[0].number);
      expect(out.error).toBe("");
    }));
  test("same, without an idempotency store (lookup by correlation_id alone)", () =>
    withSn({ createCommitThenFail: [1] }, async ({ sn, client }) => {
      const out = await createHandler({ sn: client, sleep: fastSleep })(event("c-1002"));
      expect(incidents(sn, "c-1002")).toHaveLength(1);
      expect(out.incidentNumber).toBe(incidents(sn, "c-1002")[0].number);
    }));
  test("two ambiguous failures in a row still produce one incident", () =>
    withSn({ createCommitThenFail: [1, 2] }, async ({ sn, client }) => {
      await createHandler({ sn: client, sleep: fastSleep })(event("c-1003"));
      expect(incidents(sn, "c-1003")).toHaveLength(1);
    }));
  test("a 504 that did NOT commit is retried and creates the incident", () =>
    withSn({}, async ({ sn, client }) => {
      // ordinal 2 = the POST (ordinal 1 is the correlation lookup)
      sn.faults.failStatus = { 2: 504 };
      const out = await createHandler({ sn: client, sleep: fastSleep })(event("c-1004"));
      expect(incidents(sn, "c-1004")).toHaveLength(1);
      expect(out.incidentNumber).toBe(incidents(sn, "c-1004")[0].number);
    }));
  test("429 on create is retried after Retry-After and creates one incident", () =>
    withSn({ rateLimit: [2] }, async ({ sn, client }) => {
      const out = await createHandler({ sn: client, sleep: fastSleep })(event("c-1005"));
      expect(incidents(sn, "c-1005")).toHaveLength(1);
      expect(out.error).toBe("");
    }));
});

describe("duplicate invocations for the same contact", () => {
  test("Connect retrying the Lambda (sequential re-invoke) returns the same incident and creates nothing", () =>
    withSn({}, async ({ sn, client }) => {
      const h = createHandler({ sn: client, store: new InMemoryIdempotencyStore(), sleep: fastSleep });
      const a = await h(event("c-2001"));
      const b = await h(event("c-2001"));
      expect(incidents(sn, "c-2001")).toHaveLength(1);
      expect(b.incidentNumber).toBe(a.incidentNumber);
      expect(b.created).toBe("false");
    }));
  test("re-invoke after the idempotency record was lost still finds the incident by correlation_id", () =>
    withSn({}, async ({ sn, client }) => {
      const a = await createHandler({ sn: client, store: new InMemoryIdempotencyStore(), sleep: fastSleep })(event("c-2002"));
      const b = await createHandler({ sn: client, store: new InMemoryIdempotencyStore(), sleep: fastSleep })(event("c-2002"));
      expect(incidents(sn, "c-2002")).toHaveLength(1);
      expect(b.incidentNumber).toBe(a.incidentNumber);
    }));
  test("two concurrent invocations for one contact create one incident and both return it", () =>
    withSn({ latencyMs: 120 }, async ({ sn, client }) => {
      const store = new InMemoryIdempotencyStore();
      const h = createHandler({ sn: client, store, sleep: fastSleep });
      const [a, b] = await Promise.all([h(event("c-2003")), h(event("c-2003"))]);
      expect(incidents(sn, "c-2003")).toHaveLength(1);
      expect(a.incidentNumber).toBe(incidents(sn, "c-2003")[0].number);
      expect(b.incidentNumber).toBe(a.incidentNumber);
    }));
});

describe("DynamoDB idempotency store", () => {
  test("claim is a conditional put with a TTL; a lost race returns false", async () => {
    const ddb = mockClient(DynamoDBDocumentClient);
    const doc = DynamoDBDocumentClient.from(new DynamoDBClient({ region: "us-east-1" }));
    const store = new DynamoIdempotencyStore(doc, "lfg-idempotency", () => 1_760_000_000_000);
    ddb.on(PutCommand).resolvesOnce({}).rejectsOnce(Object.assign(new Error("The conditional request failed"), { name: "ConditionalCheckFailedException" }));
    expect(await store.claim("k", 3600)).toBe(true);
    expect(await store.claim("k", 3600)).toBe(false);
    const input = ddb.commandCalls(PutCommand)[0].args[0].input;
    expect(input.ConditionExpression).toBe("attribute_not_exists(pk)");
    expect(input.Item!.expiresAt).toBe(1_760_000_000 + 3600);
    ddb.restore();
  });
});

describe("guards", () => {
  test("a non-retryable 4xx returns an error without creating anything", () =>
    withSn({}, async ({ sn, client }) => {
      sn.faults.failStatus = { 2: 403 };
      const out = await createHandler({ sn: client, sleep: fastSleep })(event("c-3001"));
      expect(out.incidentNumber).toBe("");
      expect(out.error).not.toBe("");
      expect(incidents(sn, "c-3001")).toHaveLength(0);
    }));
  test("result is a flat string map", () =>
    withSn({}, async ({ client }) => {
      const out: Record<string, unknown> = await createHandler({ sn: client, sleep: fastSleep })(event("c-3002"));
      for (const v of Object.values(out)) expect(typeof v).toBe("string");
    }));
});
