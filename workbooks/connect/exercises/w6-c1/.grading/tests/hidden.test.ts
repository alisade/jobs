// Hidden tests for connect/w6-c1 (run from tests/__hidden__).
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { startFakeServiceNow, FakeServiceNow } from "connect-kit";
import { loadBatch, parseAnalysisFile, IncompleteJobError, UnredactedInputError } from "../../src/analysis";
import { evaluateCompliance } from "../../src/compliance";
import { agentKpis } from "../../src/kpi";
import { RealtimeMonitor } from "../../src/realtime";
import { QaTaskClient } from "../../src/servicenow";
import { processBatch } from "../../src/run";
import { analysisDir, cid, contacts, fileFor, noSleep, policy, segmentEvents } from "../helpers";

const parse = (n: number) => parseAnalysisFile(fileFor(n).key, fileFor(n).body);
const ev = (n: number) => evaluateCompliance(parse(n), policy);
const client = (sn: FakeServiceNow, extra: any = {}) =>
  new QaTaskClient({ baseUrl: sn.url, clientId: sn.client.clientId, clientSecret: sn.client.clientSecret, sleep: noSleep, ...extra });

describe("parsing", () => {
  test("a FAILED job is rejected as incomplete", () => {
    expect(() => parse(8)).toThrow(IncompleteJobError);
  });
  test("a body claiming Redacted under a raw object name is still refused", () => {
    const raw = fileFor(7);
    const forged = { ...raw.body, ContentMetadata: { Output: "Redacted" } };
    expect(() => parseAnalysisFile(raw.key, forged)).toThrow(UnredactedInputError);
  });
  test("a raw body under a redacted object name is refused", () => {
    const f = fileFor(2);
    expect(() => parseAnalysisFile(f.key, { ...f.body, ContentMetadata: { Output: "Raw" } })).toThrow(UnredactedInputError);
  });
  test("loadBatch keeps 7 analyses and rejects the raw and failed files with reasons", () => {
    const b = loadBatch(analysisDir);
    expect(b.analyses.map((a) => a.contactId).sort()).toEqual([1, 2, 3, 4, 5, 6, 9].map(cid).sort());
    expect(b.rejected.map((r) => r.reason).sort()).toEqual(["INCOMPLETE", "UNREDACTED"]);
  });
});

describe("compliance", () => {
  test("missing disclosure is a priority 3 finding with no evidence turns", () => {
    const r = ev(2);
    expect(r.disclosureOk).toBe(false);
    expect(r.findings).toEqual([expect.objectContaining({ ruleId: "DISCLOSURE-PASSWORD", priority: 3, turnIds: [], atMillis: null })]);
  });
  test("asking for the caller's password is a priority 1 finding, listed first", () => {
    const r = ev(4);
    expect(r.prohibited).toBe(true);
    expect(r.findings.map((f) => f.ruleId)).toEqual(["PROHIBITED-CREDENTIAL-REQUEST", "DISCLOSURE-PASSWORD"]);
    expect(r.findings[0].atMillis).toBeGreaterThan(0);
  });
  test("a greeting after the 15 s window fails adherence even though the phrase is present", () => {
    const r = ev(5);
    expect(r.greetingOk).toBe(false);
    expect(r.adherent).toBe(false);
    expect(r.disclosureOk).toBe(true);
  });
  test("a call without a closing question fails adherence but raises no QA finding", () => {
    const r = ev(6);
    expect(r.closingOk).toBe(false);
    expect(r.findings).toEqual([]);
  });
  test("escalation evidence lists every matching customer turn, never agent turns", () => {
    const r = ev(3);
    const f = r.findings.find((x) => x.ruleId === "ESCALATION-LANGUAGE")!;
    const turns = parse(3).file.Transcript.filter((t) => f.turnIds.includes(t.Id));
    expect(turns.length).toBe(1);
    expect(turns.every((t) => t.ParticipantId === "CUSTOMER")).toBe(true);
  });
  test("chat contacts are evaluated with the same policy (punctuation and case do not matter)", () => {
    const r = ev(9);
    expect(r).toMatchObject({ greetingOk: true, closingOk: true, disclosureOk: true, findings: [] });
  });
  test("an agent saying the escalation phrase is not a customer escalation", () => {
    const a = parse(1);
    a.file.Transcript = [...a.file.Transcript, { BeginOffsetMillis: 30000, EndOffsetMillis: 31000, Id: "x", ParticipantId: "AGENT", Content: "If you like you can file a complaint online.", Sentiment: "NEUTRAL" }];
    expect(evaluateCompliance(a, policy).escalation).toBe(false);
  });
});

describe("KPIs", () => {
  const b = () => loadBatch(analysisDir);
  test("one row per agent, sorted, counting only accepted analyses", () => {
    const x = b();
    const k = agentKpis(x.analyses, x.analyses.map((a) => evaluateCompliance(a, policy)), contacts);
    expect(k.map((r) => [r.agentId, r.contacts])).toEqual([["a-jlee", 2], ["a-mgarza", 3], ["a-rpatel", 2]]);
  });
  test("sentiment averages and quarter deltas", () => {
    const x = b();
    const k = agentKpis(x.analyses, x.analyses.map((a) => evaluateCompliance(a, policy)), contacts);
    const m = k.find((r) => r.agentId === "a-mgarza")!;
    expect(m.avgCustomerSentiment).toBeCloseTo((-3.6 + 0.2 + 0.9) / 3, 2);
    expect(m.avgCustomerSentimentDelta).toBeCloseTo((0 + 2.5 + 2.5) / 3, 2);
    expect(m.escalations).toBe(1);
    expect(m.prohibited).toBe(1);
    expect(m.disclosureRate).toBeCloseTo(0.67, 2);
  });
  test("talk ratio uses only contacts with TalkTime (chat has none) and interruptions per contact", () => {
    const x = b();
    const k = agentKpis(x.analyses, x.analyses.map((a) => evaluateCompliance(a, policy)), contacts);
    const m = k.find((r) => r.agentId === "a-mgarza")!;
    const voice = [3, 4].map((n) => parse(n).file.ConversationCharacteristics.TalkTime!);
    const expected = voice.reduce((s, t) => s + t.DetailsByParticipant.AGENT!.TotalTimeMillis, 0) / voice.reduce((s, t) => s + t.TotalTimeMillis, 0);
    expect(m.agentTalkRatio).toBeCloseTo(expected, 2);
    expect(m.agentInterruptionsPerContact).toBeCloseTo(2 / 3, 2);
  });
  test("adherence rate", () => {
    const x = b();
    const k = agentKpis(x.analyses, x.analyses.map((a) => evaluateCompliance(a, policy)), contacts);
    expect(k.find((r) => r.agentId === "a-jlee")!.adherenceRate).toBe(0);
    expect(k.find((r) => r.agentId === "a-rpatel")!.adherenceRate).toBe(1);
  });
});

describe("real-time monitor", () => {
  const run = () => {
    const m = new RealtimeMonitor(policy);
    return { m, alerts: segmentEvents().flatMap((e) => m.handle(e)) };
  };
  test("partial Utterance segments never trigger an alert", () => {
    const m = new RealtimeMonitor(policy);
    const e = segmentEvents().find((x) => x.Segments && x.Segments[0].Utterance)!;
    expect(m.handle({ ...e, Segments: [{ Utterance: { ...e.Segments[0].Utterance, PartialContent: "I want to speak to your manager" } }] })).toEqual([]);
  });
  test("escalation alert carries the transcript id and offset of the first matching customer segment", () => {
    const { alerts } = run();
    const a = alerts.find((x) => x.contactId === cid(101) && x.type === "ESCALATION_LANGUAGE")!;
    expect(a).toMatchObject({ transcriptId: "rt-customer-02", atMillis: 4000 });
  });
  test("sustained negative fires once, at the third distinct negative customer segment (duplicates ignored)", () => {
    const { alerts } = run();
    const s = alerts.filter((x) => x.contactId === cid(102) && x.type === "SUSTAINED_NEGATIVE");
    expect(s).toHaveLength(1);
    expect(s[0].atMillis).toBe(11000);
  });
  test("segments after COMPLETED are ignored and the contact is no longer active", () => {
    const { m, alerts } = run();
    expect(alerts.filter((x) => x.contactId === cid(101))).toHaveLength(1);
    expect(m.active()).toEqual([]);
  });
  test("a positive or neutral customer turn resets the negative run", () => {
    const m = new RealtimeMonitor(policy);
    const base = segmentEvents()[0];
    const seg = (i: number, s: string) => ({ ...base, EventType: "SEGMENTS", Segments: [{ Transcript: { Id: `z${i}`, ParticipantId: "CUSTOMER", ParticipantRole: "CUSTOMER", Content: "hmm", BeginOffsetMillis: i * 1000, EndOffsetMillis: i * 1000 + 500, Sentiment: s } }] });
    const out = ["NEGATIVE", "NEGATIVE", "NEUTRAL", "NEGATIVE", "NEGATIVE"].flatMap((s, i) => m.handle(seg(i, s) as any));
    expect(out).toEqual([]);
  });
});

describe("ServiceNow QA tasks", () => {
  let sn: FakeServiceNow;
  afterEach(async () => sn && sn.stop());
  const input = (c = cid(3)) => ({ correlationId: `${c}:ESCALATION-LANGUAGE`, shortDescription: "QA", description: "d", priority: 2, assignmentGroup: "LFG-SD-QA" });

  test("ensureTask is idempotent by correlation_id", async () => {
    sn = await startFakeServiceNow();
    const c = client(sn);
    const a = await c.ensureTask(input());
    const b = await c.ensureTask(input());
    expect(a.created).toBe(true);
    expect(b).toMatchObject({ created: false, number: a.number });
    expect(sn.db.task).toHaveLength(1);
  });
  test("the token is cached across calls", async () => {
    sn = await startFakeServiceNow();
    const c = client(sn);
    await c.ensureTask(input(cid(1)));
    await c.ensureTask(input(cid(2)));
    expect(sn.counters.token).toBe(1);
  });
  test("a 401 after token revocation re-authenticates once and succeeds", async () => {
    sn = await startFakeServiceNow({ faults: { expireTokensAfter: 1 } });
    const c = client(sn);
    await c.ensureTask(input(cid(1)));
    await c.ensureTask(input(cid(2)));
    expect(sn.counters.token).toBe(2);
    expect(sn.db.task).toHaveLength(2);
  });
  test("429 honours Retry-After and then succeeds", async () => {
    sn = await startFakeServiceNow({ faults: { rateLimit: [1, 2], retryAfterSeconds: 2 } });
    const waits: number[] = [];
    const c = client(sn, { sleep: async (ms: number) => { waits.push(ms); } });
    const t = await c.ensureTask(input());
    expect(t.created).toBe(true);
    expect(waits).toEqual([2000, 2000]);
  });
  test("persistent 429 gives up after a bounded number of attempts with an error", async () => {
    sn = await startFakeServiceNow({ faults: { rateLimit: Array.from({ length: 50 }, (_, i) => i + 1), retryAfterSeconds: 0 } });
    const c = client(sn);
    await expect(c.ensureTask(input())).rejects.toThrow();
    expect(sn.tableRequests().length).toBeLessThanOrEqual(6);
  });
  test("bad client credentials fail fast (no retry storm)", async () => {
    sn = await startFakeServiceNow();
    const c = new QaTaskClient({ baseUrl: sn.url, clientId: "x", clientSecret: "y", sleep: noSleep });
    await expect(c.ensureTask(input())).rejects.toThrow();
    expect(sn.counters.token).toBeLessThanOrEqual(2);
  });
});

describe("processBatch end to end", () => {
  let sn: FakeServiceNow;
  afterEach(async () => sn && sn.stop());
  test("creates exactly the 4 expected QA tasks with priorities and no transcript text", async () => {
    sn = await startFakeServiceNow();
    const r = await processBatch({ dir: analysisDir, policy, contacts, sn: client(sn) });
    expect(r.processed).toBe(7);
    expect(r.tasks.map((t) => t.correlationId).sort()).toEqual([
      `${cid(2)}:DISCLOSURE-PASSWORD`, `${cid(3)}:ESCALATION-LANGUAGE`, `${cid(4)}:DISCLOSURE-PASSWORD`, `${cid(4)}:PROHIBITED-CREDENTIAL-REQUEST`,
    ].sort());
    const rows = sn.db.task;
    expect(rows).toHaveLength(4);
    expect(rows.find((x) => x.correlation_id.endsWith("PROHIBITED-CREDENTIAL-REQUEST"))!.priority).toBe("1");
    for (const row of rows) {
      expect(row.assignment_group).toBe("LFG-SD-QA");
      expect(JSON.stringify(row)).not.toMatch(/read me your password|unacceptable|\[PII\]/i);
    }
  });
  test("re-running the same batch creates nothing new", async () => {
    sn = await startFakeServiceNow();
    await processBatch({ dir: analysisDir, policy, contacts, sn: client(sn) });
    const again = await processBatch({ dir: analysisDir, policy, contacts, sn: client(sn) });
    expect(again.tasks.every((t) => !t.created)).toBe(true);
    expect(sn.db.task).toHaveLength(4);
  });
  test("a ServiceNow failure on one task is reported and does not stop the batch", async () => {
    sn = await startFakeServiceNow({ faults: { failStatus: { 2: 400 } } });
    const r = await processBatch({ dir: analysisDir, policy, contacts, sn: client(sn) });
    expect(r.taskErrors.length).toBe(1);
    expect(r.tasks.length).toBe(3);
  });
  test("an empty directory yields an empty report", async () => {
    sn = await startFakeServiceNow();
    const d = fs.mkdtempSync(path.join(os.tmpdir(), "w6c1-"));
    const r = await processBatch({ dir: d, policy, contacts, sn: client(sn) });
    expect(r).toMatchObject({ processed: 0, tasks: [], agents: [] });
  });
});
