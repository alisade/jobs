// Visible tests for connect/w5-c2. The grader adds more (filters, guardrails, budget, citations).
import { event, FINANCE, sentConverse, sentRetrieve, setup } from "./harness";

test("answers with citations mapped to KB article ids", async () => {
  const { handler } = setup();
  const r = await handler(event(FINANCE));
  expect(r.status).toBe("ANSWERED");
  expect(r.citations).toBe("KB0012345,KB0012399");
  expect(r.answer).toMatch(/Re-enroll/);
});

test("Retrieve is filtered by the caller's entitlements", async () => {
  const { handler, ar } = setup();
  await handler(event(FINANCE));
  expect(sentRetrieve(ar).retrievalConfiguration.vectorSearchConfiguration.filter).toBeDefined();
});

test("Converse runs with the configured guardrail", async () => {
  const { handler, rt } = setup();
  await handler(event(FINANCE));
  expect(sentConverse(rt).guardrailConfig).toMatchObject({ guardrailIdentifier: "gr-lfg-helpdesk", guardrailVersion: "4" });
});

test("a guardrail intervention hands off to an agent", async () => {
  const { handler } = setup({ converse: "converse-guardrail-grounding" });
  const r = await handler(event(FINANCE));
  expect(r.status).toBe("HANDOFF");
  expect(r.handoffReason).toBe("GUARDRAIL_INTERVENED");
});

test("every value returned to Connect is a string", async () => {
  const { handler } = setup();
  const r = await handler(event(FINANCE));
  for (const v of Object.values(r)) expect(typeof v).toBe("string");
});
