// Generate the incident bundle for connect/w8-t1 into incident/ (deterministic: fixed seed).
// Inputs are the committed dev inventory and prod inventory; the bundle does not depend on your fix.
const fs = require("fs");
const path = require("path");
const root = path.resolve(__dirname, "..");
const out = path.join(root, "incident");
const dev = JSON.parse(fs.readFileSync(path.join(root, "export/dev/inventory.json"), "utf8"));
const prod = JSON.parse(fs.readFileSync(path.join(root, "inventory/prod.json"), "utf8"));
const R = (inv, kind, name) => inv.resources.find((r) => r.kind === kind && r.name === name);

let seed = 20261006;
const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
const pick = (a) => a[Math.floor(rnd() * a.length)];
const hex = (n) => Array.from({ length: n }, () => "0123456789abcdef"[Math.floor(rnd() * 16)]).join("");
const uuid = () => `${hex(8)}-${hex(4)}-4${hex(3)}-8${hex(3)}-${hex(12)}`;
const t0 = Date.UTC(2026, 9, 6, 18, 30, 0);
const iso = (ms) => new Date(ms).toISOString();

fs.rmSync(out, { recursive: true, force: true });
for (const d of ["", "pipeline", "flow-logs", "lambda-logs", "metrics", "diff"]) fs.mkdirSync(path.join(out, d), { recursive: true });

fs.writeFileSync(path.join(out, "PAGE.txt"), `PagerDuty INC-7731  SEV2  triggered 2026-10-06 19:41 UTC
Service: LFG Help Desk - Amazon Connect prod (lfg-helpdesk-prod, us-east-1, 444455556666)
Alert: GeneralSupport LongestQueueWaitTime > 900 s for 15 min (threshold 300 s)

#helpdesk-ops thread
19:43 nisha.k (L1 lead, Pune): GeneralSupport is drowning. Half the callers just want a password
      reset - why are they not getting the self-service reset any more?
19:46 marco.r (agent, Monterrey): callers say they never got asked "what do you need help with",
      they go straight to hold music.
19:52 dev-oncall: identify-caller Lambda shows Init Duration ~1.8 s and a timeout at 19:07 right
      after the deploy. Cold starts? I want to add provisioned concurrency.
19:58 release-mgr: release 2026.10.06 ("natural-language front door") went out in pipeline run
      #418 at 19:05. Every stage was green, including promote.
20:01 sup-ny: VIP calls look fine.
20:04 you are paged in. Find the cause, fix it so it cannot happen again, and write it up.
`);

// --- pipeline log (GitHub Actions style)
fs.writeFileSync(path.join(out, "pipeline/run-418.log"), [
  "2026-10-06T18:58:02.114Z ##[group]Run export-dev",
  "2026-10-06T18:58:02.115Z aws connect describe-contact-flow --instance-id " + dev.instanceId + " ... (2 flows)",
  "2026-10-06T18:58:04.902Z aws connect describe-contact-flow-module ... (2 modules)",
  "2026-10-06T18:58:05.010Z ##[endgroup]",
  "2026-10-06T18:58:05.311Z ##[group]Run unit-tests",
  "2026-10-06T18:59:40.772Z Tests: 214 passed, 214 total",
  "2026-10-06T18:59:40.900Z ##[endgroup]",
  "2026-10-06T18:59:41.002Z ##[group]Run promote (target=prod)",
  "2026-10-06T18:59:41.410Z node scripts/run-ts.js pipeline/release.ts",
  "2026-10-06T18:59:41.988Z promote: 4 artifacts, 17 references rewritten; check-refs: 0 problem(s)",
  "2026-10-06T18:59:42.001Z check-refs: gate not implemented (REL-412), skipped",
  "2026-10-06T18:59:42.010Z ##[endgroup]",
  "2026-10-06T18:59:42.300Z ##[group]Run lint-flows",
  "2026-10-06T18:59:42.912Z validateFlow: 4 artifacts, 0 errors, 0 warnings",
  "2026-10-06T18:59:42.950Z ##[endgroup]",
  "2026-10-06T19:00:10.002Z ##[group]Run approve-prod (environment: production, reviewers: cab-helpdesk)",
  "2026-10-06T19:04:51.640Z Approved by j.ortega",
  "2026-10-06T19:04:51.700Z ##[endgroup]",
  "2026-10-06T19:04:52.100Z ##[group]Run deploy-prod",
  "2026-10-06T19:04:53.004Z aws connect update-contact-flow-module-content mod-after-hours ... OK",
  "2026-10-06T19:04:53.611Z aws connect update-contact-flow-module-content mod-password-reset ... OK",
  "2026-10-06T19:04:54.213Z aws connect update-contact-flow-content \"LFG Help Desk Inbound\" ... OK",
  "2026-10-06T19:04:54.820Z aws connect update-contact-flow-content \"LFG Major Incident\" ... OK",
  "2026-10-06T19:04:55.002Z aws lambda update-function-code lfg-identify-caller (2026.10.06) ... OK; publish version 41; alias live -> 41",
  "2026-10-06T19:05:01.330Z ##[endgroup]",
  "2026-10-06T19:05:01.900Z ##[group]Run smoke (synthetic call +1 800 555 0142, DTMF '2')",
  "2026-10-06T19:05:48.215Z smoke: reached queue GeneralSupport in 41 s -> PASS",
  "2026-10-06T19:05:48.300Z ##[endgroup]",
  "",
].join("\n"));

// --- flow logs (CloudWatch Logs export, one JSON per line; simplified field set)
const inboundId = R(prod, "flow", "LFG Help Desk Inbound").id;
const prodAlias = R(prod, "lexAlias", "HelpDeskBot/live").arn;
const devAlias = R(dev, "lexAlias", "HelpDeskBot/live").arn;
const lines = [];
const contacts = [];
let t = t0;
const release = Date.UTC(2026, 9, 6, 19, 5, 0);
for (let i = 0; i < 64; i++) {
  t += 20000 + Math.floor(rnd() * 60000);
  if (t > Date.UTC(2026, 9, 6, 19, 40, 0)) break;
  const cid = uuid();
  const after = t >= release;
  const timedOut = after && t >= Date.UTC(2026, 9, 6, 19, 7, 0) && t < Date.UTC(2026, 9, 6, 19, 7, 50);
  const vip = rnd() < 0.08;
  const intent = pick(["ResetPassword", "ResetPassword", "ResetPassword", "GeneralIssue", "GeneralIssue", "ReportOutage"]);
  let ts = t;
  const log = (identifier, type, params, results) => {
    ts += 300 + Math.floor(rnd() * 900);
    const e = { ContactId: cid, ContactFlowId: `${prod.instanceArn}/contact-flow/${inboundId}`, ContactFlowName: "LFG Help Desk Inbound", ContactFlowModuleType: type, Identifier: identifier, Timestamp: iso(ts), Parameters: params };
    if (results !== undefined) e.Results = results;
    lines.push(e);
  };
  log("start-logging", "SetLoggingBehavior", { LoggingBehavior: "Enable" });
  log("check-hours", "CheckHoursOfOperation", { Hours: "HelpDeskHours" }, "True");
  log("identify-caller", "InvokeExternalResource", { FunctionArn: R(prod, "lambda", "lfg-identify-caller").arn + ":live", TimeLimit: "3000" }, timedOut ? "Failed" : "Success");
  log(timedOut ? "set-unverified" : "set-verified", "SetAttributes", { Key: "callerVerified", Value: timedOut ? "false" : "true" });
  log("check-vip", "CheckAttribute", { Namespace: "User Defined", Key: "vip", ComparisonValue: vip ? "true" : "false" }, vip ? "true" : "NoMatch");
  let queue;
  if (vip) {
    queue = "VIPDesk";
  } else if (!after) {
    // release 2026.09.29: DTMF menu, no bot
    log("main-menu", "GetUserInput", { Text: "For password resets, press 1. For hardware or software problems, press 2. To report an outage, press 3." }, intent === "ResetPassword" ? "1" : intent === "ReportOutage" ? "3" : "2");
    queue = intent === "ResetPassword" ? (rnd() < 0.7 ? null : "PasswordReset") : intent === "ReportOutage" ? "MajorIncident" : "GeneralSupport";
    if (intent === "ResetPassword") log("password-module", "InvokeFlowModule", { FlowModuleName: "mod-password-reset" }, queue ? "FAILED" : "SENT");
  } else {
    log("ask-bot", "GetUserInput", { BotAliasArn: devAlias, Text: "In a few words, tell me what you need help with." }, "Error");
    queue = "GeneralSupport";
  }
  if (queue) {
    log(`set-q-${queue === "GeneralSupport" ? "general" : queue === "PasswordReset" ? "password" : queue === "VIPDesk" ? "vip" : "major"}`, "SetQueue", { Queue: R(prod, "queue", queue).arn });
    log("transfer", "TransferContactToQueue", {}, "Success");
  } else {
    log("disconnect", "Disconnect", {});
  }
  contacts.push({ cid, t, after, intent, queue: queue || "SELF_SERVICE", vip });
}
fs.writeFileSync(path.join(out, "flow-logs/aws-connect-lfg-helpdesk-prod-2026-10-06.jsonl"), lines.map((l) => JSON.stringify(l)).join("\n") + "\n");

// --- identify-caller Lambda logs (the red herring)
const ll = [];
let lt = Date.UTC(2026, 9, 6, 19, 6, 40);
for (let i = 0; i < 18; i++) {
  lt += 30000 + Math.floor(rnd() * 70000);
  const rid = uuid();
  const cold = i < 3;
  const timeout = i === 1;
  ll.push(`${iso(lt)} START RequestId: ${rid} Version: 41`);
  if (timeout) {
    ll.push(`${iso(lt + 3001)} ${rid} Task timed out after 3.00 seconds`);
    ll.push(`${iso(lt + 3002)} END RequestId: ${rid}`);
    ll.push(`${iso(lt + 3002)} REPORT RequestId: ${rid} Duration: 3000.00 ms Billed Duration: 3000 ms Memory Size: 512 MB Max Memory Used: 141 MB Init Duration: 1842.11 ms Status: timeout`);
  } else {
    const d = cold ? 2100 + Math.floor(rnd() * 400) : 80 + Math.floor(rnd() * 120);
    ll.push(`${iso(lt + d - 5)} ${rid} INFO directory lookup ok employee=E1${String(Math.floor(rnd() * 9999)).padStart(4, "0")} vip=false ms=${d - 40}`);
    ll.push(`${iso(lt + d)} END RequestId: ${rid}`);
    ll.push(`${iso(lt + d)} REPORT RequestId: ${rid} Duration: ${d}.00 ms Billed Duration: ${d} ms Memory Size: 512 MB Max Memory Used: 138 MB${cold ? ` Init Duration: ${1700 + Math.floor(rnd() * 200)}.42 ms` : ""}`);
  }
}
fs.writeFileSync(path.join(out, "lambda-logs/lfg-identify-caller-2026-10-06.log"), ll.join("\n") + "\n");

// --- queue / containment metrics (15-minute intervals)
const rows = ["interval_start_utc,queue,contacts_queued,contacts_handled,longest_wait_s,self_service_resets"];
for (let m = 0; m < 6; m++) {
  const start = t0 + m * 900000;
  const inWin = contacts.filter((c) => c.t >= start && c.t < start + 900000);
  for (const q of ["GeneralSupport", "PasswordReset", "VIPDesk", "MajorIncident"]) {
    const n = inWin.filter((c) => c.queue === q).length * 9;
    const after = start >= release - 300000;
    const wait = q === "GeneralSupport" ? (after ? 300 + m * 180 : 95 + Math.floor(rnd() * 40)) : 40 + Math.floor(rnd() * 60);
    rows.push(`${iso(start)},${q},${n},${Math.max(0, n - (after && q === "GeneralSupport" ? 20 : 2))},${wait},${q === "PasswordReset" ? inWin.filter((c) => c.queue === "SELF_SERVICE").length * 9 : ""}`);
  }
}
fs.writeFileSync(path.join(out, "metrics/queue-intervals.csv"), rows.join("\n") + "\n");
fs.writeFileSync(path.join(out, "metrics/cloudwatch-AWS-Connect.txt"), [
  "Namespace AWS/Connect  InstanceId " + prod.instanceId + "  period 5 min  statistic Sum",
  "time(UTC)  ContactFlowErrors  ContactFlowFatalErrors  ThrottledCalls  MissedCalls",
  "18:45      0                  0                       0               0",
  "19:00      0                  0                       0               0",
  "19:05      11                 0                       0               0",
  "19:10      24                 0                       0               0",
  "19:15      22                 0                       0               1",
  "19:20      26                 0                       0               0",
  "19:25      21                 0                       0               0",
  "19:30      25                 0                       0               2",
  "",
].join("\n"));

// --- diff of the inbound flow: release 2026.09.29 (deployed) vs 2026.10.06 (deployed)
fs.writeFileSync(path.join(out, "diff/inbound-2026.09.29-to-2026.10.06.diff"), `--- deployed/2026.09.29/LFG Help Desk Inbound (prod)
+++ deployed/2026.10.06/LFG Help Desk Inbound (prod)
@@ check-vip @@
-        "NoMatchingCondition" -> "main-menu"
+        "NoMatchingCondition" -> "ask-bot"
@@ -main-menu (GetParticipantInput, DTMF) +ask-bot (ConnectParticipantWithLexBot) @@
-  { "Identifier": "main-menu", "Type": "GetParticipantInput",
-    "Parameters": { "Text": "For password resets, press 1. For hardware or software problems, press 2. To report an outage, press 3.", ... },
-    "Transitions": { "Conditions": [ "1" -> "password-module", "2" -> "set-q-general", "3" -> "to-major-incident" ], ... } }
+  { "Identifier": "ask-bot", "Type": "ConnectParticipantWithLexBot",
+    "Parameters": { "Text": "In a few words, tell me what you need help with.",
+                    "LexV2Bot": { "AliasArn": "${devAlias}" },
+                    "LexSessionAttributes": { "callerVerified": "$.Attributes.callerVerified" } },
+    "Transitions": { "Conditions": [ "ResetPassword" -> "password-module", "ReportOutage" -> "to-major-incident",
+                                     "GeneralIssue" -> "set-q-general" ],
+                     "Errors": [ InputTimeLimitExceeded, NoMatchingCondition, NoMatchingError -> "set-q-general" ] } }
@@ identify-caller @@
   "LambdaFunctionARN": "${R(prod, "lambda", "lfg-identify-caller").arn}:live"   (unchanged; alias live -> version 41 in this release)
`);
fs.writeFileSync(path.join(out, "README.txt"), `Incident bundle for connect/w8-t1 (generated by make setup; regenerate with make bundle).
PAGE.txt                  the page and the ops thread
pipeline/run-418.log      the release pipeline run that shipped 2026.10.06
flow-logs/*.jsonl         Connect flow logs for the prod inbound flow, 18:30-19:40 UTC (simplified field set)
lambda-logs/*.log         identify-caller Lambda logs after the deploy
metrics/                  queue intervals and AWS/Connect CloudWatch metrics
diff/                     what changed in the inbound flow between the two prod releases
The prod inventory is ../inventory/prod.json; the dev export is ../export/dev/; the artifacts that were
deployed are ../release/prod/ (as committed, before your fix).
`);
console.log(`incident bundle written to ${path.relative(process.cwd(), out) || out}`);
