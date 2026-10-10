// Visible tests for connect/w7-c1 (happy path). The grader adds edge cases and failure paths.
import { setup, teardown, baseEvent, Env } from "./harness";

let env: Env;
afterEach(async () => teardown(env));

test("known caller: creates an incident and returns a flat string map", async () => {
  env = await setup();
  const out = await env.handler(baseEvent());
  expect(out.status).toBe("OK");
  expect(out.employeeFound).toBe("true");
  expect(out.employeeId).toBe("E10442");
  expect(out.incidentCreated).toBe("true");
  expect(out.incidentNumber).toMatch(/^INC\d{7}$/);
  for (const v of Object.values(out)) expect(typeof v).toBe("string");
});

test("the incident carries the caller, the phone channel and the contact id as correlation_id", async () => {
  env = await setup();
  await env.handler(baseEvent());
  const created = env.sn.db.incident.find((r) => r.correlation_id === "6a1f0c2e-8d4b-4f7e-b3a9-0c5d2e7f9a11");
  expect(created).toBeDefined();
  expect(created!.caller_id).toBe("a1b2c3d4e5f60718293a4b5c6d7e8f90");
  expect(created!.contact_type).toBe("phone");
});

test("open incident count only counts the caller's active incidents", async () => {
  env = await setup();
  const out = await env.handler({ ...baseEvent(), Details: { ...baseEvent().Details, Parameters: { action: "lookup" } } });
  expect(out.openIncidentCount).toBe("3");
  expect(out.incidentCreated).toBe("false");
});
