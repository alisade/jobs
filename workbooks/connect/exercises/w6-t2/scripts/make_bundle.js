#!/usr/bin/env node
// Generates the incident bundle for connect/w6-t2 into incident/ (deterministic). Run via make setup / make bundle.
"use strict";
const fs = require("fs");
const path = require("path");
const root = path.resolve(__dirname, "..");
const out = path.join(root, "incident");
fs.rmSync(out, { recursive: true, force: true });
const W = (rel, data) => {
  const p = path.join(out, rel);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, typeof data === "string" ? data : JSON.stringify(data, null, 2) + "\n");
};
const INST = "arn:aws:connect:us-east-1:111122223333:instance/5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f";
const Q = { GeneralSupport: "q-general-support", PasswordReset: "q-password-reset", VIPDesk: "q-vip-desk", MajorIncident: "q-major-incident" };
const cid = (n) => `b5d8e2f1-${String(n).padStart(4, "0")}-4a3b-8c7d-${String(n).padStart(12, "0")}`;

W("PAGE.txt", `LFG-2290  P3  "Live escalation alerts never fire"   opened 2026-10-07 by Mei Tanaka (QA lead)
-------------------------------------------------------------------------------------------
Since go-live of CHG0034502 (2026-09-30) supervisors should get an alert email while a caller is still
on the line when they say things like "speak to your supervisor". Three callers escalated this week
(contacts in the attached flow logs) and the floor supervisors got nothing until the next morning,
when the post-call category "Escalation-Weekly" showed up in the QA dashboard.

-- thread --
10:02 Arjun (Connect admin, Pune): rule "Escalation language - live" is PUBLISHED, trigger is real-time,
      queues GeneralSupport + PasswordReset, phrases copied from the weekly rule. The weekly one works.
10:15 Arjun: the segment-stream consumer had IteratorAgeMilliseconds spikes on Monday, maybe real-time
      analytics is backed up? See incident/metrics/kinesis-iterator-age.txt
10:31 Mei: CHG0034502 added "Set recording and analytics behavior" with Real-time at the top of the inbound
      flow. Arjun tested it in the sandbox flow and the alert fired there.
10:40 Dev (supervisor, Monterrey): we can see the live transcript for a few seconds in the IVR, then it stops.
`);

const rule = (name, source, modes) => ({
  Rule: {
    Name: name, RuleId: name === "Escalation language - live" ? "0b7c2f2e-1d4a-4e8b-9a61-5c3d2e1f0a11" : "6e2a9d10-3b4c-4d5e-8f60-7a8b9c0d1e22",
    RuleArn: `${INST}/rule/${name.replace(/ /g, "-").toLowerCase()}`,
    TriggerEventSource: { EventSourceName: source },
    Function: JSON.stringify({ Version: "2022-11-25", RuleFunction: { Operator: "AND", Operands: [
      { Operator: "CONTAINS_ANY", Operands: ["speak to your supervisor", "speak to your manager", "file a complaint", "this is unacceptable"],
        ComparisonValue: `$.ContactLens.${modes}.ExactMatch.Transcript`, FilterClause: { LogicOperator: "AND", Filters: [{ Type: "ParticipantRole", Data: "CUSTOMER" }] }, Negate: false },
      { Operator: "CONTAINS_ANY", Operands: [Q.GeneralSupport, Q.PasswordReset], ComparisonValue: `$.ContactLens.${modes}.Queue.QueueId`, Negate: false },
    ] } }),
    Actions: source === "OnRealTimeCallAnalysisAvailable"
      ? [{ ActionType: "SEND_NOTIFICATION", SendNotificationAction: { DeliveryMethod: "EMAIL", Subject: "Live escalation on $.ContactLens.RealTimeCall.Queue.QueueId", Content: "Caller is asking for a supervisor. Contact: $.ContactId", ContentType: "PLAIN_TEXT", Recipient: { UserIds: ["sup-dvega", "sup-mtanaka"] } } },
         { ActionType: "GENERATE_EVENTBRIDGE_EVENT", EventBridgeAction: { Name: "LIVE_ESCALATION" } }]
      : [{ ActionType: "ASSIGN_CONTACT_CATEGORY", AssignContactCategoryAction: {} }, { ActionType: "GENERATE_EVENTBRIDGE_EVENT", EventBridgeAction: { Name: "WEEKLY_ESCALATION" } }],
    PublishStatus: "PUBLISHED", LastUpdatedTime: "2026-09-30T14:02:11Z", LastUpdatedBy: "arn:aws:connect:...:agent/a-amehta",
  },
});
W("rules/escalation-language-live.describe-rule.json", rule("Escalation language - live", "OnRealTimeCallAnalysisAvailable", "RealTimeCall"));
W("rules/escalation-weekly.describe-rule.json", rule("Escalation-Weekly", "OnPostCallAnalysisAvailable", "PostCall"));

// flow logs (CloudWatch Logs /aws/connect/lfg-helpdesk, fields abridged) for the three escalated calls
const lines = [];
const ts = (n, s) => `2026-10-0${5 + (n % 3)}T14:${String(10 + n).padStart(2, "0")}:${String(s).padStart(2, "0")}.${String(100 + s * 7).slice(-3)}Z`;
const analytics = (modes) => ({ VoiceBehavior: { VoiceRecordingBehavior: { RecordedParticipants: ["Agent", "Customer"] }, VoiceAnalyticsBehavior: { Enabled: "True", AnalyticsLanguage: "en-US", AnalyticsModes: modes, ConversationalAnalyticsRedactionConfiguration: { Enabled: "True", RedactionResults: "RedactedOnly" } } } });
for (const [n, queue, keys] of [[1, "GeneralSupport", ["2"]], [2, "PasswordReset", ["1"]], [3, "GeneralSupport", ["9", "2"]]]) {
  const log = (s, id, type, params, results, flow = "LFG Help Desk Inbound") =>
    lines.push(JSON.stringify({ Timestamp: ts(n, s), ContactId: cid(n), ContactFlowName: flow, ContactFlowModuleType: type, Identifier: id, Parameters: params, Results: results }));
  log(0, "start-logging", "UpdateFlowLoggingBehavior", { FlowLoggingBehavior: "Enabled" }, "Success");
  log(1, "set-analytics", "UpdateContactRecordingAndAnalyticsBehavior", analytics(["RealTime"]), "Success");
  log(1, "check-hours", "CheckHoursOfOperation", { HoursOfOperationId: "hoo-helpdesk" }, "True");
  log(2, "identify-caller", "InvokeLambdaFunction", { FunctionArn: "arn:aws:lambda:us-east-1:111122223333:function:lfg-identify-caller", TimeLimit: "3" }, "Success");
  log(3, "main-menu", "GetParticipantInput", { Text: "For password resets, press 1. ..." }, keys[keys.length - 1]);
  if (queue === "PasswordReset") {
    log(5, "password-reset", "InvokeLambdaFunction", { FunctionArn: "arn:aws:lambda:us-east-1:111122223333:function:lfg-password-reset", TimeLimit: "6" }, "Success");
    log(6, "check-reset", "Compare", { ComparisonValue: "FAILED" }, "NoMatchingCondition");
  }
  log(7, `set-q-${queue === "PasswordReset" ? "password" : "general"}`, "UpdateContactTargetQueue", { QueueId: `${INST}/queue/${Q[queue]}` }, "Success");
  log(8, "check-staffing", "CheckMetricData", { MetricType: "NumberOfAgentsStaffed" }, "True");
  log(8, "apply-recording-defaults", "InvokeFlowModule", { FlowModuleId: "mod-recording-defaults" }, "Success");
  log(9, "set-recording", "UpdateContactRecordingAndAnalyticsBehavior", analytics(["PostContact"]), "Success", "mod-recording-defaults");
  log(9, "done", "EndFlowModuleExecution", {}, "Success", "mod-recording-defaults");
  log(10, "transfer", "TransferContactToQueue", { QueueId: `${INST}/queue/${Q[queue]}` }, "Success");
}
W("flow-logs/aws-connect-lfg-helpdesk.jsonl", lines.join("\n") + "\n");

// post-call output excerpts: the phrase is there and the weekly category matched
const said = ["Honestly, I want to speak to your supervisor right now.", "This is unacceptable, third reset this month.", "I will file a complaint about this."];
for (const n of [1, 2, 3]) {
  W(`analysis/${cid(n)}_analysis_redacted_excerpt.json`, {
    Version: "1.1.0", Channel: "VOICE", ContentMetadata: { Output: "Redacted", RedactionTypes: ["PII"] }, JobStatus: "COMPLETED", LanguageCode: "en-US",
    Categories: { MatchedCategories: ["Escalation-Weekly"], MatchedDetails: { "Escalation-Weekly": { PointsOfInterest: [{ BeginOffsetMillis: 61000 + n * 1000, EndOffsetMillis: 65000 + n * 1000 }] } } },
    Transcript: [{ BeginOffsetMillis: 61000 + n * 1000, EndOffsetMillis: 65000 + n * 1000, Id: `t9-${n}`, ParticipantId: "CUSTOMER", Content: said[n - 1], Sentiment: "NEGATIVE" }],
  });
}
// EventBridge archive: only post-call matches
W("eventbridge/archive-lfg-connect-rules.jsonl", [1, 2, 3].map((n) => JSON.stringify({
  version: "0", id: `evb-${n}`, source: "aws.connect", "detail-type": "conversational analytics Post Call Rules Matched", account: "111122223333",
  time: `2026-10-0${5 + (n % 3)}T14:${String(31 + n)}:02Z`, region: "us-east-1", resources: [INST],
  detail: { version: "1.0", ruleName: "Escalation-Weekly", actionName: "WEEKLY_ESCALATION", instanceArn: INST, contactArn: `${INST}/contact/${cid(n)}`, agentArn: `${INST}/agent/a-rpatel`, queueArn: `${INST}/queue/${Q.GeneralSupport}` },
})).join("\n") + "\n");
W("metrics/kinesis-iterator-age.txt", `CloudWatch  AWS/Kinesis  GetRecords.IteratorAgeMilliseconds  StreamName=lfg-connect-ca-segments  (Maximum, 5 min)
2026-10-05 09:00  1,240
2026-10-05 09:05  118,900   <- consumer redeploy (lfg-ca-segment-consumer v2.3.1)
2026-10-05 09:10  2,310
2026-10-05 14:10  1,020
2026-10-06 14:10    980
2026-10-07 14:10  1,110
Note: lfg-connect-ca-segments is the stream configured for real-time contact analysis segments; its
consumer feeds the agent-coaching dashboard. It is not part of rule evaluation.
`);
W("change/CHG0034502.txt", `CHG0034502  Real-time escalation alerts for supervisors   implemented 2026-09-30 by Arjun Mehta
1. Inbound flow "LFG Help Desk Inbound" v14: add Set recording and analytics behavior (Real-time) as 2nd block.
2. Create rule "Escalation language - live" (real-time, queues GeneralSupport/PasswordReset, notify supervisors).
3. Tested in "Sandbox Inbound" flow (no modules) - alert received in 40 s.  Rollback: unpublish rule.
Not changed: module mod-recording-defaults v3 (LFG-1302, March 2026, PCI redaction defaults before transfer).
`);
console.log("incident bundle written to incident/");
