#!/usr/bin/env node
// Generates the incident bundle for connect/w6-t1 into incident/ (deterministic). Run via make setup / make bundle.
// The S3 mirror follows the documented conversational analytics layout:
//   Analysis/Voice/YYYY/MM/DD/<contactId>_analysis_<ts>.json                 (original, only with RedactedAndOriginal)
//   Analysis/Voice/Redacted/YYYY/MM/DD/<contactId>_analysis_redacted_<ts>.json (redacted)
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
const BUCKET = "s3/lfg-connect-us-east-1/connect/lfg-helpdesk";
const cid = (n) => `7e3b9a10-${String(n).padStart(4, "0")}-4c2d-9e8f-${String(n).padStart(12, "0")}`;
const ENT = ["CREDIT_DEBIT_NUMBER", "NAME", "USERNAME", "PASSWORD", "PHONE", "EMAIL", "SSN"];

// contacts: [n, date, agent, issueRaw, issueRedacted, sentiment]
const contacts = [
  [1, "2026-09-20", "a-rpatel", "My VPN keeps dropping every ten minutes.", null, 1.2],
  [2, "2026-09-20", "a-mgarza", "My corporate card 4111 1111 1111 1111 is declined in Concur and I'm locked out.", "My corporate card [PII] is declined in Concur and I'm locked out.", -1.4],
  [3, "2026-09-21", "a-jlee", "Outlook keeps asking for my password since the update.", null, -0.2],
  [4, "2026-09-23", "a-rpatel", "I need the Finance SharePoint site, my manager is Dana Ruiz.", "I need the Finance SharePoint site, my manager is [PII].", 0.4],
  [5, "2026-09-24", "a-mgarza", "Expense report rejected, the card ending 5500 0000 0000 0004 shows as invalid.", "Expense report rejected, the card ending [PII] shows as invalid.", -2.1],
  [6, "2026-09-26", "a-jlee", "Laptop fan is loud and it overheats in meetings.", null, -0.6],
  [7, "2026-09-29", "a-rpatel", "Okta Verify stopped working after I changed phones.", null, 0.8],
  [8, "2026-10-01", "a-mgarza", "Travel card 3782 822463 10005 was charged twice for the hotel.", "Travel card [PII] was charged twice for the hotel.", -2.8],
  [9, "2026-10-02", "a-jlee", "Printer on floor 12 jams on every job.", null, -0.3],
  [10, "2026-10-05", "a-rpatel", "Teams crashes when I share my screen.", null, -0.9],
  [11, "2026-10-06", "a-mgarza", "Card 6011-1111-1111-1117 was blocked by the procurement portal.", "Card 6011-1111-1111-1117 was blocked by the procurement portal.", -1.7],
  [12, "2026-10-07", "a-jlee", "Need a loaner laptop for the board offsite.", null, 1.5],
];
const ORIGINALS_FROM = "2026-09-22"; // flow changed to RedactedAndOriginal on 2026-09-22 (CHG0034417)

function analysis(c, output) {
  const [n, date, , issueRaw, issueRed, sent] = c;
  const issue = output === "Raw" ? issueRaw : issueRed || issueRaw;
  const meta = output === "Raw" ? { Output: "Raw" } : {
    Output: "Redacted", RedactionTypes: ["PII"],
    RedactionTypesMetadata: { PII: { RedactionEntitiesRequested: ENT, RedactionMaskMode: "PII" } },
  };
  const t1 = { BeginOffsetMillis: 0, EndOffsetMillis: 4200, Id: `t0-${n}`, ParticipantId: "AGENT", Content: "Thank you for calling Larkspur IT service desk, this is [PII].", Sentiment: "NEUTRAL" };
  const t2 = { BeginOffsetMillis: 4500, EndOffsetMillis: 9800, Id: `t1-${n}`, ParticipantId: "CUSTOMER", Content: issue, Sentiment: sent < 0 ? "NEGATIVE" : "NEUTRAL",
    IssuesDetected: [{ CharacterOffsets: { BeginOffsetChar: 0, EndOffsetChar: issue.length }, Text: issue }] };
  if (output !== "Raw" && issueRed) t2.Redaction = { RedactedTimestamps: [{ BeginOffsetMillis: 6100, EndOffsetMillis: 7900 }] };
  return {
    Version: "1.1.0", AccountId: "111122223333", Channel: "VOICE", ContentMetadata: meta, JobStatus: "COMPLETED", LanguageCode: "en-US",
    Participants: [{ ParticipantId: "CUSTOMER", ParticipantRole: "CUSTOMER" }, { ParticipantId: "AGENT", ParticipantRole: "AGENT" }],
    Categories: { MatchedCategories: /card/i.test(issueRaw) ? ["Finance-Card"] : [], MatchedDetails: {} },
    ConversationCharacteristics: { TotalConversationDurationMillis: 182000 + n * 1000, Sentiment: { OverallSentiment: { AGENT: 0.5, CUSTOMER: sent } } },
    Transcript: [t1, t2],
  };
}

const listing = [];
for (const c of contacts) {
  const [n, date] = c;
  const [y, m, d] = date.split("-");
  const ts = `${date}T15-${String(10 + n).padStart(2, "0")}-00Z`;
  const red = `${BUCKET}/Analysis/Voice/Redacted/${y}/${m}/${d}/${cid(n)}_analysis_redacted_${ts}.json`;
  W(red, analysis(c, "Redacted"));
  listing.push(`${date} 15:${String(14 + n).padStart(2, "0")}:07     ${String(4800 + n * 37).padStart(7)} ${red.replace(/^s3\/lfg-connect-us-east-1\//, "")}`);
  if (date >= ORIGINALS_FROM) {
    const raw = `${BUCKET}/Analysis/Voice/${y}/${m}/${d}/${cid(n)}_analysis_${ts}.json`;
    W(raw, analysis(c, "Raw"));
    listing.push(`${date} 15:${String(14 + n).padStart(2, "0")}:05     ${String(4700 + n * 37).padStart(7)} ${raw.replace(/^s3\/lfg-connect-us-east-1\//, "")}`);
  }
}
W("s3-listing.txt", "$ aws s3 ls --recursive s3://lfg-connect-us-east-1/connect/lfg-helpdesk/Analysis/Voice/\n" + listing.sort().join("\n") + "\n");

W("PAGE.txt", `SEV-2  SEC-INC-7781  opened 2026-10-08 08:12 ET by Finance Controllership (Priya Natarajan)
--------------------------------------------------------------------------------------
Subject: card numbers visible in the "Service desk contact drivers" report

The weekly contact-drivers CSV that QA shares with Finance (qa-insights/contact-drivers-2026-10-07.csv)
shows full corporate card numbers in the issue_snippet column. We were told in the June design review
that Connect redacts card numbers from call analytics before anything leaves the contact center.
Finance has paused the report distribution. PCI QSA notified per policy. We need root cause, a fix,
and confirmation of what else was exposed.

-- thread --
08:31 Mei (QA lead): the report job has not changed since June except the dedupe fix two weeks ago.
08:40 Arjun (Connect admin, Pune): redaction is on in the flow, CREDIT_DEBIT_NUMBER is in the entity list.
      I noticed CVV and expiry are NOT in the list, maybe that is it?
08:52 Mei: also odd, the Sept 20-21 rows disappeared when I re-ran the report for September.
09:05 Sam (security): CloudTrail shows the report role reading objects under Analysis/Voice/. Pulling details.
`);
W("report/contact-drivers-2026-10-07.csv", "contact_id,date,agent_id,categories,customer_sentiment,issue_snippet\n" +
  contacts.filter((c) => c[1] >= ORIGINALS_FROM).map((c) => `${cid(c[0])},${c[1]},${c[2]},${/card/i.test(c[3]) ? "Finance-Card" : ""},${c[5]},"${c[3]}"`).join("\n") + "\n");
W("change/CHG0034417-flow-analytics-block.diff", `--- flows/helpdesk-inbound.json  (published 2026-06-30)
+++ flows/helpdesk-inbound.json  (published 2026-09-22, CHG0034417 "Legal hold: keep original transcripts for 7 years")
@@ action set-recording-analytics (UpdateContactRecordingAndAnalyticsBehavior)
         "ConversationalAnalyticsRedactionConfiguration": {
           "Enabled": "True",
-          "RedactionResults": "RedactedOnly",
+          "RedactionResults": "RedactedAndOriginal",
           "RedactionMaskMode": "PII",
           "RedactionEntities": ["CREDIT_DEBIT_NUMBER", "NAME", "USERNAME", "PASSWORD", "PHONE", "EMAIL", "SSN"]
         },
`);
W("flows/helpdesk-inbound.analytics-block.json", {
  Identifier: "set-recording-analytics", Type: "UpdateContactRecordingAndAnalyticsBehavior",
  Parameters: { VoiceBehavior: {
    VoiceRecordingBehavior: { RecordedParticipants: ["Agent", "Customer"], IVRRecordingBehavior: "Disabled" },
    VoiceAnalyticsBehavior: { Enabled: "True", AnalyticsLanguage: "en-US", AnalyticsModes: ["PostContact"],
      ConversationalAnalyticsRedactionConfiguration: { Enabled: "True", RedactionResults: "RedactedAndOriginal", RedactionMaskMode: "PII", RedactionEntities: ENT },
      SentimentConfiguration: { Enabled: "True" }, SummaryConfiguration: { SummaryModes: ["PostContact"] } } } },
  Transitions: { NextAction: "check-hours", Errors: [{ NextAction: "check-hours", ErrorType: "NoMatchingError" }, { NextAction: "check-hours", ErrorType: "ChannelMismatch" }] },
});
W("repo/git-log.txt", `commit 4be1c07  2026-09-24  Mei Tanaka   fix duplicate rows in QA report (LFG-2231)
    Report showed every contact twice since Monday. Skip the Redacted/ folder so each contact is listed once.
commit 91aa3d2  2026-06-28  Arjun Mehta  contact drivers report: first version (LFG-1904)
`);
W("repo/LFG-2231.txt", `LFG-2231  Contact drivers report lists every call twice   (opened 2026-09-23 by Mei Tanaka)
Since 09-22 each contact appears twice in contact-drivers.csv with the same contact id. Probably the job.
Resolution 2026-09-24: excluded the Redacted/ subfolder in the S3 listing. Duplicates gone. Closed.
`);
W("cloudtrail/report-role-getobject.jsonl", contacts.filter((c) => c[1] >= ORIGINALS_FROM).slice(0, 4).map((c) => JSON.stringify({
  eventTime: "2026-10-07T23:05:1" + (c[0] % 10) + "Z", eventSource: "s3.amazonaws.com", eventName: "GetObject",
  userIdentity: { type: "AssumedRole", arn: "arn:aws:sts::111122223333:assumed-role/lfg-qa-report-job/report-batch" },
  requestParameters: { bucketName: "lfg-connect-us-east-1", key: `connect/lfg-helpdesk/Analysis/Voice/${c[1].replace(/-/g, "/")}/${cid(c[0])}_analysis_${c[1]}T15-${String(10 + c[0]).padStart(2, "0")}-00Z.json` },
})).join("\n") + "\n");
console.log("incident bundle written to incident/");
