"use strict";
// Generates the incident bundle for connect/w4-t1 into incident/ (deterministic).
// Runs the validation harness against the CURRENT config, so after a fix `make bundle` shows the
// report going green (the PAGE, CTRs, flow logs and diff are fixed artifacts of the incident).
const fs = require("fs");
const path = require("path");
const { runSuite, report } = require("../tools/validate");
const { toLocal } = require("../tools/hours");

const ROOT = path.resolve(__dirname, "..");
const out = path.join(ROOT, "incident");
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(path.join(out, "flow-logs"), { recursive: true });
const w = (p, s) => fs.writeFileSync(path.join(out, p), s.endsWith("\n") ? s : s + "\n");

w("PAGE.txt", `INC0049231  P3  Wave 2 parallel run: migrated help desk number fails validation
Opened 2026-10-09 21:12 ET by Priya Natarajan (Pune migration factory lead)

Wave 2 moves VDN 47100 / vector 14 (main help desk, +1 800 555 0142) to Connect. Before we port
the number (scheduled Mon 2026-10-19 06:00 ET) the parallel-run gate needs 100% of the
validation suite green. Tonight's run: see validation-report.txt. Factory reviewed the
translated flow line by line against the vector (PR #212) and it matches.

--- #lfg-connect-wave2 (Slack export) ---
[16:52] Marco (Monterrey night shift lead): test calls to the parallel-run DID at 16:40 got
        "the help desk is closed". Our shift starts at 16:00.
[16:58] Ana (QA): same at 17:15 and 18:30. 15:30 was fine.
[17:20] Jordan (Connect admin): yesterday's release 2026.10.08 changed the VIP routing profile
        (delay on general queue 0 -> 30 s), maybe that? see release-2026.10.08.diff
[17:41] Priya: holiday cases for Columbus Day (Mon 10/12) all pass in the report.
[18:05] Ana: also odd: a 03:10 test call reached the menu and sat in queue. Avaya would have
        played the closed message at 03:10.
[18:30] Jordan: CloudWatch flow logs for two contacts attached (flow-logs/). CTR export from the
        parallel-run DID attached (ctr-parallel-run.jsonl).

Ask: find the root cause, fix it in the migration repo, prove the suite is green including
across the DST change on Sun 2026-11-01, and explain why the factory's review missed it.
`);

w("validation-report.txt", `Migration validation: vector 14 (Avaya CM, America/New_York) vs flows/helpdesk-inbound-migrated.json
Run: 2026-10-09 21:00 ET  dates (NY): 2026-10-09, 2026-10-12, 2026-10-13  every 30 min x 4 key paths
${report(runSuite(["2026-10-09", "2026-10-12", "2026-10-13"]))}`);

// Flow logs (CloudWatch Logs, log group /aws/connect/lfg-helpdesk), one JSON event per line.
const flowArn = "arn:aws:connect:us-east-1:111122223333:instance/5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f/contact-flow/cf-hd-main-wave2";
const hoo = "arn:aws:connect:us-east-1:111122223333:instance/5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f/operating-hours/hoo-helpdesk";
const hol = "arn:aws:connect:us-east-1:111122223333:instance/5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f/operating-hours/hoo-helpdesk-holidays";
function flowLog(contactId, t0, events) {
  let t = Date.parse(t0);
  return events
    .map(([type, id, results, params]) => {
      t += 380;
      return JSON.stringify({ ContactId: contactId, ContactFlowId: flowArn, ContactFlowName: "LFG HD Main (wave 2)", ContactFlowModuleType: type, Identifier: id, Timestamp: new Date(t).toISOString(), ...(results ? { Results: results } : {}), Parameters: params || {} });
    })
    .join("\n");
}
w("flow-logs/7f3c2a10-5b1e-4f7a-9d2e-61b0c4e8a901.jsonl", flowLog("7f3c2a10-5b1e-4f7a-9d2e-61b0c4e8a901", "2026-10-09T20:40:03.112Z", [
  ["SetLoggingBehavior", "UpdateFlowLoggingBehavior", null, { LoggingBehavior: "Enable" }],
  ["SetAttributes", "UpdateContactAttributes", null, { Key: "digits", Value: "" }],
  ["CheckHoursOfOperation", "step-01-goto", "True", { HoursOfOperation: hol }],
  ["CheckHoursOfOperation", "step-02-goto", "False", { HoursOfOperation: hoo }],
  ["PlayPrompt", "step-16-disconnect", null, { Text: "The Larkspur IT help desk is closed. Our hours are 6 AM to 8 PM Eastern. Goodbye." }],
  ["Disconnect", "disconnect", null, {}],
]));
w("flow-logs/0c9d1e22-8a4b-4c6d-b2f1-3e5a7d9c0b14.jsonl", flowLog("0c9d1e22-8a4b-4c6d-b2f1-3e5a7d9c0b14", "2026-10-09T07:10:41.507Z", [
  ["SetLoggingBehavior", "UpdateFlowLoggingBehavior", null, { LoggingBehavior: "Enable" }],
  ["SetAttributes", "UpdateContactAttributes", null, { Key: "digits", Value: "" }],
  ["CheckHoursOfOperation", "step-01-goto", "True", { HoursOfOperation: hol }],
  ["CheckHoursOfOperation", "step-02-goto", "True", { HoursOfOperation: hoo }],
  ["PlayPrompt", "step-03-announcement", null, { Text: "Welcome to the Larkspur IT help desk." }],
  ["GetUserInput", "step-04-collect", "2", { Text: "For password resets, press 1. ..." }],
  ["SetAttributes", "set-digits", null, { Key: "digits", Value: "2" }],
  ["SetQueue", "step-12-queue-to", null, { Queue: "arn:aws:connect:us-east-1:111122223333:instance/5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f/queue/q-general-support" }],
  ["CheckStaffing", "check-agents-3", "True", { MetricType: "NumberOfAgentsStaffed" }],
  ["SetRoutingBehavior", "set-priority-3", null, { QueuePriority: "3" }],
  ["TransferToQueue", "transfer-3", null, {}],
]));

// Contact records from the parallel-run DID (abridged CTR fields).
const ctrs = [
  ["2026-10-09T13:31:02Z", 41, null, "CONTACT_FLOW_DISCONNECT", "2"],
  ["2026-10-09T15:05:40Z", 388, "q-general-support", "AGENT_DISCONNECT", "2"],
  ["2026-10-09T19:30:12Z", 402, "q-password-reset", "CUSTOMER_DISCONNECT", "1"],
  ["2026-10-09T20:40:03Z", 19, null, "CONTACT_FLOW_DISCONNECT", ""],
  ["2026-10-09T21:15:44Z", 18, null, "CONTACT_FLOW_DISCONNECT", ""],
  ["2026-10-09T22:30:09Z", 19, null, "CONTACT_FLOW_DISCONNECT", ""],
  ["2026-10-09T23:48:51Z", 18, null, "CONTACT_FLOW_DISCONNECT", ""],
  ["2026-10-09T07:10:41Z", 912, "q-general-support", "CUSTOMER_DISCONNECT", "2"],
  ["2026-10-09T08:02:13Z", 640, "q-major-incident", "CUSTOMER_DISCONNECT", "3"],
];
w("ctr-parallel-run.jsonl", ctrs
  .map(([ts, secs, q, reason, digits], i) => JSON.stringify({
    ContactId: `pr-${String(i + 1).padStart(4, "0")}-${ts.slice(11, 13)}${ts.slice(14, 16)}`,
    Channel: "VOICE",
    InitiationMethod: "INBOUND",
    InitiationTimestamp: ts,
    DisconnectTimestamp: new Date(Date.parse(ts) + secs * 1000).toISOString().replace(".000", ""),
    SystemEndpoint: { Address: "+18005550177", Type: "TELEPHONE_NUMBER" },
    Queue: q ? { Name: q, ARN: `arn:aws:connect:us-east-1:111122223333:instance/5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f/queue/${q}` } : null,
    Agent: reason === "AGENT_DISCONNECT" ? { Username: "mrios" } : null,
    DisconnectReason: reason,
    Attributes: { digits },
    Tags: { "lfg:test": "parallel-run" },
  }))
  .join("\n"));

w("release-2026.10.08.diff", `commit 9e41c07 (tag: release-2026.10.08)
Author: Jordan Ellis <jordan.ellis@larkspur.example>
Date:   Thu Oct 8 18:02:11 2026 -0400

    Wave 2: VIP desk overflow to general queue after 30 s; flow metadata

diff --git a/config/routing-profiles.json b/config/routing-profiles.json
@@ -21,7 +21,7 @@
       { "Queue": "q-vip-desk", "Channel": "VOICE", "Priority": 1, "Delay": 0 },
-      { "Queue": "q-general-support", "Channel": "VOICE", "Priority": 2, "Delay": 0 }
+      { "Queue": "q-general-support", "Channel": "VOICE", "Priority": 2, "Delay": 30 }
     ]
diff --git a/flows/helpdesk-inbound-migrated.json b/flows/helpdesk-inbound-migrated.json
@@ -3,7 +3,7 @@
   "Metadata": {
-    "name": "LFG HD Main (migrated from vector 14) DRAFT",
+    "name": "LFG HD Main (migrated from vector 14)",
`);

const sample = toLocal("2026-10-09T20:40:03Z", "America/New_York");
w("README.txt", `Bundle generated by make setup (scripts/make-bundle.js). Times in AWS artifacts are UTC.
Example: 2026-10-09T20:40:03Z is ${sample.date} ${sample.time} in New York.
Re-run the suite yourself: node tools/validate.js --dates 2026-10-09,2026-11-02`);
console.log("incident bundle written to incident/");
