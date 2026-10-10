// Hidden tests for connect/w6-t2 (run from tests/__hidden__).
import { ANALYTICS, effectiveAtTransfer, inbound, moduleFlow, rule, Path } from "../helpers";

const paths: Path[] = ["general", "password", "vip", "afterhours-outage"];

describe.each(paths)("path %s", (p) => {
  test("reaches a queue", () => {
    expect(effectiveAtTransfer(p).result.outcome).toBe("TransferredToQueue");
  });
  test("real-time analytics is the effective mode at transfer", () => {
    const a = effectiveAtTransfer(p).analytics;
    expect(a.VoiceAnalyticsBehavior.Enabled).toBe("True");
    expect(a.VoiceAnalyticsBehavior.AnalyticsModes).toContain("RealTime");
  });
  test("PCI redaction defaults still apply (enabled, redacted only)", () => {
    const r = effectiveAtTransfer(p).analytics.VoiceAnalyticsBehavior.ConversationalAnalyticsRedactionConfiguration;
    expect(r).toMatchObject({ Enabled: "True", RedactionResults: "RedactedOnly" });
    expect(r.RedactionEntities).toEqual(expect.arrayContaining(["CREDIT_DEBIT_NUMBER", "PASSWORD", "SSN"]));
  });
  test("the recording-defaults module is still applied before the transfer", () => {
    expect(effectiveAtTransfer(p).moduleBeforeTransfer).toBe(true);
  });
});

test("every analytics block records both participants in en-US and handles NoMatchingError and ChannelMismatch", () => {
  const blocks = [...inbound().Actions, ...moduleFlow().Actions].filter((a) => a.Type === ANALYTICS);
  expect(blocks.length).toBeGreaterThan(0);
  for (const b of blocks) {
    const v = b.Parameters.VoiceBehavior;
    expect(v.VoiceRecordingBehavior.RecordedParticipants.sort()).toEqual(["Agent", "Customer"]);
    expect(v.VoiceAnalyticsBehavior.AnalyticsLanguage).toBe("en-US");
    expect((b.Transitions.Errors || []).map((e) => e.ErrorType).sort()).toEqual(["ChannelMismatch", "NoMatchingError"]);
  }
});

test("no analytics block in the call path selects PostContact (it would switch real-time off)", () => {
  const blocks = [...inbound().Actions, ...moduleFlow().Actions].filter((a) => a.Type === ANALYTICS);
  for (const b of blocks) expect(b.Parameters.VoiceBehavior.VoiceAnalyticsBehavior.AnalyticsModes).not.toContain("PostContact");
});

test("the rule stays a published real-time rule on both queues with the customer phrase condition", () => {
  const r = rule();
  expect(r.TriggerEventSource.EventSourceName).toBe("OnRealTimeCallAnalysisAvailable");
  expect(r.PublishStatus).toBe("PUBLISHED");
  const ops = r.Function.RuleFunction.Operands;
  const phrase = ops.find((o: any) => o.ComparisonValue === "$.ContactLens.RealTimeCall.ExactMatch.Transcript");
  expect(phrase.FilterClause.Filters[0].Data).toBe("CUSTOMER");
  const q = ops.find((o: any) => o.ComparisonValue === "$.ContactLens.RealTimeCall.Queue.QueueId");
  expect(q.Operands.sort()).toEqual(["q-general-support", "q-password-reset"]);
});
