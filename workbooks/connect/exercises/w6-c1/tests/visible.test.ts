// Visible tests for connect/w6-c1. The grader adds hidden tests (edge cases, failure paths, idempotency).
import { startFakeServiceNow } from "connect-kit";
import { parseAnalysisFile, UnredactedInputError } from "../src/analysis";
import { evaluateCompliance } from "../src/compliance";
import { agentKpis } from "../src/kpi";
import { RealtimeMonitor } from "../src/realtime";
import { QaTaskClient } from "../src/servicenow";
import { cid, contacts, fileFor, noSleep, policy, segmentEvents } from "./helpers";

test("a redacted, completed analysis parses and keeps the contact id from the object name", () => {
  const f = fileFor(1);
  const a = parseAnalysisFile(f.key, f.body);
  expect(a.contactId).toBe(cid(1));
  expect(a.channel).toBe("VOICE");
});

test("a raw (unredacted) analysis is refused", () => {
  const f = fileFor(7);
  expect(() => parseAnalysisFile(f.key, f.body)).toThrow(UnredactedInputError);
});

test("a clean call meets greeting, closing and disclosure with no findings", () => {
  const f = fileFor(1);
  const r = evaluateCompliance(parseAnalysisFile(f.key, f.body), policy);
  expect(r).toMatchObject({ greetingOk: true, closingOk: true, disclosureOk: true, adherent: true, escalation: false, prohibited: false });
  expect(r.findings).toEqual([]);
});

test("customer escalation language is a priority 2 finding with evidence turns", () => {
  const f = fileFor(3);
  const r = evaluateCompliance(parseAnalysisFile(f.key, f.body), policy);
  const esc = r.findings.find((x) => x.ruleId === "ESCALATION-LANGUAGE")!;
  expect(esc.priority).toBe(2);
  expect(esc.turnIds.length).toBeGreaterThan(0);
});

test("agent KPIs aggregate per agent", () => {
  const as = [1, 2].map((n) => parseAnalysisFile(fileFor(n).key, fileFor(n).body));
  const rs = as.map((a) => evaluateCompliance(a, policy));
  const k = agentKpis(as, rs, contacts);
  expect(k).toHaveLength(1);
  expect(k[0]).toMatchObject({ agentId: "a-rpatel", contacts: 2, disclosureRate: 0.5 });
});

test("real-time: escalation phrase in a final customer transcript raises one alert", () => {
  const m = new RealtimeMonitor(policy);
  const alerts = segmentEvents().flatMap((e) => m.handle(e));
  expect(alerts.filter((a) => a.contactId === cid(101) && a.type === "ESCALATION_LANGUAGE")).toHaveLength(1);
});

test("creates a QA task in ServiceNow", async () => {
  const sn = await startFakeServiceNow();
  try {
    const c = new QaTaskClient({ baseUrl: sn.url, clientId: sn.client.clientId, clientSecret: sn.client.clientSecret, sleep: noSleep });
    const t = await c.ensureTask({ correlationId: `${cid(3)}:ESCALATION-LANGUAGE`, shortDescription: "QA review", description: "x", priority: 2, assignmentGroup: "LFG-SD-QA" });
    expect(t.created).toBe(true);
    expect(t.number).toMatch(/^TASK/);
    expect(sn.db.task).toHaveLength(1);
  } finally {
    await sn.stop();
  }
});
