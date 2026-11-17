// Hidden tests for connect/w7-c1 (run from tests/__hidden__).
import { SearchProfilesCommand } from "@aws-sdk/client-customer-profiles";
import { setup, teardown, baseEvent, Env, incidentsFor, seedUsers, CONTACT_ID, snmod, applyServiceNowDefaults } from "../harness";

let env: Env;
afterEach(async () => teardown(env));
const u1 = seedUsers[0].sys_id;
const tableCalls = (e: Env, pathPart: string) => e.sn.tableRequests().filter((r) => r.path.includes(pathPart));

describe("identity", () => {
  test("Customer Profiles is searched by the _phone key with the E.164 caller number", async () => {
    env = await setup();
    await env.handler(baseEvent());
    const calls = env.profiles.commandCalls(SearchProfilesCommand);
    expect(calls.length).toBe(1);
    expect(calls[0].args[0].input).toMatchObject({ DomainName: "lfg-employees", KeyName: "_phone", Values: ["+12125550187"] });
  });
  test("no profile: NOT_FOUND, no ServiceNow writes", async () => {
    env = await setup({ profileItems: [] });
    const out = await env.handler(baseEvent());
    expect(out.status).toBe("NOT_FOUND");
    expect(out.employeeFound).toBe("false");
    expect(env.sn.requests.filter((r) => r.method === "POST" && r.path.includes("/table/")).length).toBe(0);
  });
  test("two profiles share the number (shared desk phone): AMBIGUOUS, nothing created", async () => {
    env = await setup({ profileItems: [{ ProfileId: "p1", AccountNumber: "E10442" }, { ProfileId: "p2", AccountNumber: "E20001" }] });
    const out = await env.handler(baseEvent());
    expect(out.status).toBe("AMBIGUOUS");
    expect(env.sn.db.incident.filter((r) => r.correlation_id === CONTACT_ID)).toHaveLength(0);
  });
  test("sys_user lookup filters on employee_number AND active=true via sysparm_query", async () => {
    env = await setup();
    await env.handler(baseEvent());
    const q = tableCalls(env, "/sys_user")[0].query.sysparm_query;
    expect(q).toContain("employee_number=E10442");
    expect(q).toContain("active=true");
  });
  test("queries ask only for the fields they need (sysparm_fields)", async () => {
    env = await setup();
    await env.handler(baseEvent());
    for (const r of tableCalls(env, "/table/").filter((x) => x.method === "GET")) expect(r.query.sysparm_fields).toBeTruthy();
  });
  test("malformed phone number: BAD_REQUEST without calling anything", async () => {
    env = await setup();
    const ev = baseEvent();
    ev.Details.ContactData.CustomerEndpoint.Address = "anonymous";
    const out = await env.handler(ev);
    expect(out.status).toBe("BAD_REQUEST");
    expect(env.profiles.commandCalls(SearchProfilesCommand).length).toBe(0);
  });
});

describe("pagination", () => {
  test("Link rel=next is parsed (path and query preserved)", () => {
    expect(snmod.nextLink('</api/now/table/incident?sysparm_limit=2&sysparm_offset=2>;rel="next"')).toBe("/api/now/table/incident?sysparm_limit=2&sysparm_offset=2");
    expect(snmod.nextLink('<https://x.service-now.com/api/now/table/incident?sysparm_offset=4>;rel="next",<https://x.service-now.com/api/now/table/incident?sysparm_offset=0>;rel="first"')).toBe("/api/now/table/incident?sysparm_offset=4");
    expect(snmod.nextLink(null)).toBeNull();
    expect(snmod.nextLink('</api/now/table/incident?sysparm_offset=0>;rel="first"')).toBeNull();
  });
  test("all pages are read: count is right with a page size of 2", async () => {
    env = await setup({ pageSize: 2, incidents: incidentsFor(u1, 7) });
    const out = await env.handler({ ...baseEvent(), Details: { ...baseEvent().Details, Parameters: { action: "lookup" } } });
    expect(out.openIncidentCount).toBe("7");
    expect(tableCalls(env, "/table/incident").length).toBe(4);
  });
  test("idempotency guard sees an existing incident on the LAST page", async () => {
    const existing = { number: "INC0009999", caller_id: u1, active: "true", state: "1", short_description: "from first attempt", correlation_id: CONTACT_ID, sys_created_on: "2026-09-01 00:00:00" };
    env = await setup({ pageSize: 2, incidents: incidentsFor(u1, 5, [existing]) });
    const out = await env.handler(baseEvent());
    expect(out.incidentCreated).toBe("false");
    expect(out.incidentNumber).toBe("INC0009999");
    expect(env.sn.db.incident.filter((r) => r.correlation_id === CONTACT_ID)).toHaveLength(1);
  });
});

describe("idempotency and retries", () => {
  test("invoking twice for the same contact creates exactly one incident", async () => {
    env = await setup();
    const a = await env.handler(baseEvent());
    applyServiceNowDefaults(env); // ServiceNow sets active=true on a new incident
    const b = await env.handler(baseEvent());
    expect(env.sn.db.incident.filter((r) => r.correlation_id === CONTACT_ID)).toHaveLength(1);
    expect(b.incidentNumber).toBe(a.incidentNumber);
    expect(b.incidentCreated).toBe("false");
  });
  test("429 with Retry-After is honored and the call succeeds", async () => {
    env = await setup({ faults: { rateLimit: [2], retryAfterSeconds: 2 } });
    const out = await env.handler(baseEvent());
    expect(out.status).toBe("OK");
    expect(env.clock.waits).toContain(2000);
  });
  test("a Retry-After that does not fit the budget degrades instead of sleeping past Connect's limit", async () => {
    env = await setup({ faults: { rateLimit: [1, 2, 3, 4, 5], retryAfterSeconds: 30 } });
    const out = await env.handler(baseEvent());
    expect(out.status).toBe("DEGRADED");
    expect(env.clock.waits.every((w) => w < 6500)).toBe(true);
  });
  test("persistent 429s stop after a bounded number of retries", async () => {
    env = await setup({ faults: { rateLimit: Array.from({ length: 40 }, (_, i) => i + 1), retryAfterSeconds: 0 } });
    const out = await env.handler(baseEvent());
    expect(out.status).toBe("DEGRADED");
    expect(env.sn.tableRequests().length).toBeLessThanOrEqual(6);
  });
  test("ServiceNow 5xx returns DEGRADED (flat map), never throws into the flow", async () => {
    env = await setup({ faults: { failStatus: { 1: 503 } } });
    const out = await env.handler(baseEvent());
    expect(out.status).toBe("DEGRADED");
    for (const v of Object.values(out)) expect(typeof v).toBe("string");
  });
  test("total time stays inside the configured budget (< 8 s Connect limit)", async () => {
    env = await setup({ faults: { rateLimit: [1, 2, 3], retryAfterSeconds: 3 }, budgetMs: 6500 });
    await env.handler(baseEvent());
    expect(env.clock.waits.reduce((a, b) => a + b, 0)).toBeLessThan(6500);
  });
});

describe("OAuth", () => {
  test("one token for the whole invocation, reused on the next warm invocation", async () => {
    env = await setup();
    await env.handler(baseEvent());
    const ev2 = baseEvent();
    ev2.Details.ContactData.ContactId = "7b2f0c2e-8d4b-4f7e-b3a9-0c5d2e7f9a12";
    await env.handler(ev2);
    expect(env.sn.counters.token).toBe(1);
  });
  test("token revoked mid-call (401): refreshed once and the request retried", async () => {
    env = await setup({ faults: { expireTokensAfter: 1 } });
    const out = await env.handler(baseEvent());
    expect(out.status).toBe("OK");
    expect(env.sn.counters.token).toBe(2);
  });
  test("a token near expiry is refreshed before use", async () => {
    env = await setup({ faults: { tokenTtlSeconds: 90 } });
    await env.handler(baseEvent());
    await env.clock.sleep(40_000); // 40 s later the token has < 60 s left
    const ev2 = baseEvent();
    ev2.Details.ContactData.ContactId = "8c2f0c2e-8d4b-4f7e-b3a9-0c5d2e7f9a13";
    await env.handler(ev2);
    expect(env.sn.counters.token).toBe(2);
  });
  test("client credentials go in the form body, never in the query string", async () => {
    env = await setup();
    await env.handler(baseEvent());
    const tok = env.sn.requests.find((r) => r.path === "/oauth_token.do")!;
    expect(Object.keys(tok.query)).toHaveLength(0);
    expect(tok.body).toContain("grant_type=client_credentials");
  });
});

describe("contract", () => {
  test("VIP flag comes back for the flow to route on", async () => {
    env = await setup({ profileItems: [{ ProfileId: "p9", AccountNumber: "E20001" }], incidents: [] });
    const out = await env.handler(baseEvent());
    expect(out.vip).toBe("true");
    expect(out.openIncidentCount).toBe("1");
  });
  test("encoded-query injection in the employee number is neutralized", async () => {
    env = await setup({ profileItems: [{ ProfileId: "p9", AccountNumber: "E10442^ORactive=true" }] });
    await env.handler(baseEvent());
    const q = tableCalls(env, "/sys_user")[0].query.sysparm_query;
    expect(q).not.toMatch(/\^ORactive/);
  });
  test("short description is capped at 160 characters", async () => {
    env = await setup();
    const ev = baseEvent();
    ev.Details.Parameters.shortDescription = "x".repeat(400);
    await env.handler(ev);
    const created = env.sn.db.incident.find((r) => r.correlation_id === CONTACT_ID)!;
    expect(created.short_description.length).toBeLessThanOrEqual(160);
  });
});
