// Generate the incident bundle for connect/w1-t1 into incident/ (deterministic).
// It replays the afternoon of 2026-10-07 through the flow that was DEPLOYED that day
// (scripts/data/helpdesk-inbound.2026.10.07.json), not through your working copy.
"use strict";
const fs = require("fs");
const path = require("path");
const k = require("connect-kit");

const root = path.resolve(__dirname, "..");
const out = path.join(root, "incident");
const res = require(path.join(root, "config/resources.json"));
const deployed = require("./data/helpdesk-inbound.2026.10.07.json");
const previous = require("./data/helpdesk-inbound.2026.09.30.json");
const Q = res.queues;
const FLOW_ARN = `${res.instanceArn}/contact-flow/7d3e9a41-5c2b-4f0e-8a61-0e9b2c4d5f13`;

let seed = 20261007;
function rand() {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
}
const pick = (arr) => arr[Math.floor(rand() * arr.length)];
const uuid = () => "xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx".replace(/x/g, () => Math.floor(rand() * 16).toString(16));

// UI block names as they appear in flow logs, by flow-language action type.
const MODULE = {
  UpdateFlowLoggingBehavior: "SetLoggingBehavior",
  CheckHoursOfOperation: "CheckHoursOfOperation",
  InvokeLambdaFunction: "InvokeExternalResource",
  UpdateContactAttributes: "SetAttributes",
  Compare: "CheckAttribute",
  UpdateContactTargetQueue: "SetQueue",
  UpdateContactRoutingBehavior: "SetRoutingBehavior",
  Loop: "Loop",
  GetParticipantInput: "GetUserInput",
  MessageParticipant: "PlayPrompt",
  CheckMetricData: "CheckStaffing",
  TransferContactToQueue: "Transfer",
  DisconnectParticipant: "Disconnect",
};
const DURATION = { MessageParticipant: 6, GetParticipantInput: 7, InvokeLambdaFunction: 1, Loop: 0, TransferContactToQueue: 1 };

function staffingAt(minute) {
  // minute = minutes after 13:00 local (17:00Z). PasswordReset analysts in Okta MFA training 14:00-15:30.
  const prTraining = minute >= 60 && minute < 150;
  return {
    [Q.GeneralSupport]: { NumberOfAgentsStaffed: 9 },
    [Q.PasswordReset]: { NumberOfAgentsStaffed: prTraining ? 0 : 3 },
    [Q.VIPDesk]: { NumberOfAgentsStaffed: 2 },
    [Q.MajorIncident]: { NumberOfAgentsStaffed: 2 },
  };
}

function resultOf(a, branch) {
  if (a.Type === "CheckMetricData") return branch.startsWith("Condition:") ? "True" : branch.startsWith("False:") ? "False" : branch;
  if (branch === "NextAction") return "Success";
  if (branch.startsWith("Error:")) return "Error: " + branch.slice(6);
  if (branch.startsWith("Condition:") || branch === "ContinueLooping" || branch === "DoneLooping") return branch.replace(/^Condition:/, "");
  return branch;
}

function iso(ms) {
  return new Date(ms).toISOString().replace(/\.\d{3}Z$/, ".000Z");
}

function main() {
  fs.rmSync(out, { recursive: true, force: true });
  fs.mkdirSync(path.join(out, "flow-logs"), { recursive: true });
  fs.mkdirSync(path.join(out, "exported-flows"), { recursive: true });
  const logLines = [];
  const ctrs = [];
  const lambdaLines = [];
  const base = Date.UTC(2026, 9, 7, 17, 0, 0); // 13:00 America/New_York
  for (let i = 0; i < 64; i++) {
    const minute = Math.floor((i * 180) / 64) + Math.floor(rand() * 2);
    const start = base + minute * 60000 + Math.floor(rand() * 50000);
    const contactId = uuid();
    const vip = rand() < 0.08;
    const option = pick(["1", "1", "2", "2", "2", "3"]);
    const resetOk = rand() < 0.55;
    const okta429 = rand() < 0.25;
    const sim = k.simulate(deployed, {
      contactId,
      customerEndpoint: `+1212555${String(1000 + i).slice(-4)}`,
      inputs: [option],
      hours: { [res.hoursOfOperation.HelpDeskHours]: true },
      lambdas: {
        [res.lambdas.identifyCaller]: () => ({ employeeId: `E${10000 + i * 7}`, vip: vip ? "true" : "false", department: pick(["Finance", "Lending", "Ops", "HR"]) }),
        [res.lambdas.passwordReset]: () => ({ resetStatus: resetOk ? "SENT" : "FAILED" }),
      },
      lambdaLatencyMs: { [res.lambdas.identifyCaller]: 300, [res.lambdas.passwordReset]: okta429 ? 2900 : 900 },
      metrics: staffingAt(minute),
      maxSteps: 400,
    });
    // A looping caller hangs up after hearing the busy message a few times.
    let trace = sim.trace;
    let reason;

    if (sim.outcome === "StepLimit") {

      const hearings = 3 + Math.floor(rand() * 9);
      let seen = 0;
      const cut = trace.findIndex((t) => t.id === "overflow-msg" && ++seen === hearings);
      trace = trace.slice(0, cut + 1);
      reason = "CUSTOMER_DISCONNECT";
    } else if (sim.outcome === "TransferredToQueue") reason = rand() < 0.1 ? "CUSTOMER_DISCONNECT" : "AGENT_DISCONNECT";
    else reason = "CONTACT_FLOW_DISCONNECT";
    let t = start;
    for (const step of trace) {
      const a = deployed.Actions.find((x) => x.Identifier === step.id);
      const params = { ...a.Parameters };
      if (a.Type === "CheckMetricData") params.MetricType = a.Parameters.MetricType;
      const line = {
        Results: resultOf(a, step.branch),
        ContactId: contactId,
        ContactFlowId: FLOW_ARN,
        ContactFlowName: "LFG Help Desk Inbound",
        ContactFlowModuleType: MODULE[a.Type] || a.Type,
        Identifier: a.Identifier,
        Timestamp: iso(t),
        Parameters: params,
      };
      if (a.Type === "InvokeLambdaFunction") {
        line.ExternalResults = a.Parameters.LambdaFunctionARN === res.lambdas.passwordReset ? { resetStatus: resetOk ? "SENT" : "FAILED" } : { employeeId: `E${10000 + i * 7}`, vip: vip ? "true" : "false" };
      }
      logLines.push(JSON.stringify(line));
      t += (DURATION[a.Type] || 0.2) * 1000;
    }
    for (const call of sim.lambdaCalls.filter((c) => c.arn === res.lambdas.passwordReset)) {
      const rid = uuid();
      lambdaLines.push(`${iso(start + 20000)} START RequestId: ${rid} Version: $LATEST`);
      if (okta429) {
        lambdaLines.push(`${iso(start + 20400)}\t${rid}\tWARN\tokta: POST /api/v1/users/${call.payload.Details.Parameters.employeeId || "unknown"}/lifecycle/reset_password -> 429 Too Many Requests (x-rate-limit-remaining: 0); retry 1/2 after 1500 ms`);
        lambdaLines.push(`${iso(start + 22300)}\t${rid}\tINFO\tokta: retry succeeded`);
      }
      lambdaLines.push(`${iso(start + 22900)}\t${rid}\tINFO\tresetStatus=${resetOk ? "SENT" : "FAILED"} channel=sms`);
      lambdaLines.push(`${iso(start + 23000)} END RequestId: ${rid}`);
      lambdaLines.push(`${iso(start + 23000)} REPORT RequestId: ${rid}\tDuration: ${okta429 ? "2874.12" : "912.40"} ms\tBilled Duration: ${okta429 ? 2875 : 913} ms\tMemory Size: 256 MB\tMax Memory Used: 91 MB`);
    }
    const queued = sim.outcome === "TransferredToQueue";
    ctrs.push({
      ContactId: contactId,
      Channel: "VOICE",
      InitiationMethod: "INBOUND",
      InitiationTimestamp: iso(start),
      DisconnectTimestamp: iso(t + (queued ? 240000 : 0)),
      DisconnectReason: reason,
      CustomerEndpoint: { Type: "TELEPHONE_NUMBER", Address: `+1212555${String(1000 + i).slice(-4)}` },
      SystemEndpoint: { Type: "TELEPHONE_NUMBER", Address: "+18005550142" },
      Queue: queued ? { ARN: sim.queue, Name: Object.keys(Q).find((n) => Q[n] === sim.queue), EnqueueTimestamp: iso(t) } : null,
      Agent: queued && reason === "AGENT_DISCONNECT" ? { Username: pick(["mrivera", "aokafor", "jchen", "pdesai", "lgarcia"]) } : null,
      Attributes: sim.attributes,
    });
  }
  fs.writeFileSync(path.join(out, "flow-logs", "aws-connect-lfg-helpdesk-prod-2026-10-07.log"), logLines.join("\n") + "\n");
  fs.writeFileSync(path.join(out, "contact-records-2026-10-07.jsonl"), ctrs.map((c) => JSON.stringify(c)).join("\n") + "\n");
  fs.writeFileSync(path.join(out, "lambda-lfg-password-reset-2026-10-07.log"), lambdaLines.join("\n") + "\n");
  fs.writeFileSync(path.join(out, "exported-flows", "helpdesk-inbound.2026.09.30.json"), JSON.stringify(previous, null, 2) + "\n");
  fs.writeFileSync(path.join(out, "exported-flows", "helpdesk-inbound.2026.10.07.json"), JSON.stringify(deployed, null, 2) + "\n");
  const rows = ["timestamp_utc,queue,agents_staffed,agents_available,contacts_in_queue,oldest_contact_age_s"];
  for (let m = 0; m < 180; m += 15) {
    const s = staffingAt(m);
    for (const [name, arn] of Object.entries(Q)) {
      const staffed = s[arn].NumberOfAgentsStaffed;
      rows.push(`${iso(base + m * 60000)},${name},${staffed},${Math.max(0, staffed - 2 - (m % 2))},${name === "GeneralSupport" ? 3 + (m % 4) : 0},${name === "GeneralSupport" ? 40 + m : 0}`);
    }
  }
  fs.writeFileSync(path.join(out, "realtime-queue-metrics-2026-10-07.csv"), rows.join("\n") + "\n");
  fs.writeFileSync(path.join(out, "cloudwatch-metrics-2026-10-07.txt"), [
    "Namespace AWS/Connect  InstanceId 5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f  period 5m  (summed per hour, local time)",
    "metric                      13:00  14:00  15:00",
    "CallsPerInterval              21     22     21",
    "ConcurrentCallsPercentage    0.04   0.11   0.05   (max)",
    "ContactFlowErrors              0      0      0",
    "ContactFlowFatalErrors         0      0      0",
    "MissedCalls                    0      0      0",
    "ThrottledCalls                 0      0      0",
    "",
    "Namespace AWS/Lambda  FunctionName lfg-password-reset",
    "Errors                         0      0      0",
    "Throttles                      0      0      0",
    "Duration p99 (ms)            2880   2891   2874",
    "",
  ].join("\n"));
  fs.writeFileSync(path.join(out, "PAGE.txt"), [
    "PagerDuty  P2  LFG-HELPDESK-VOICE  triggered 2026-10-07 14:21 ET",
    "Summary: Help desk callers stuck hearing 'all specialists are busy' on repeat, then hang up",
    "",
    "#helpdesk-cutover thread (excerpt)",
    "14:09 Dana (Service desk lead, Charlotte): three people on my floor say the help desk 'just keeps saying the",
    "      specialists are busy, connecting you to the general help desk' and never connects. One said 2 minutes.",
    "14:12 Ravi (Pune, L2 platform): Contact search shows calls ending with CUSTOMER_DISCONNECT, no queue. CloudWatch",
    "      ContactFlowErrors is 0. Nothing failing in Connect as far as I can see.",
    "14:15 Marcus (IAM): Okta rate-limited our reset API this morning, lfg-password-reset is logging 429s. Probably that?",
    "14:18 Dana: it's not only password resets, I just tried option 2 myself. Same loop.",
    "14:20 Ravi: yesterday's release 2026.10.07 went out at 07:00 ET (CHG-48211). Morning was fine.",
    "14:24 Tom (WFM): FYI the password reset team is in Okta MFA training 14:00-15:30, 0 staffed on PasswordReset.",
    "",
    "You are the Connect lead on call. Find the root cause, fix the flow, and explain it to the CAB.",
    "",
  ].join("\n"));
  fs.writeFileSync(path.join(out, "release-notes-2026.10.07.md"), [
    "# Release 2026.10.07 - LFG Help Desk Inbound (CHG-48211)",
    "",
    "- Overflow: after moving a caller to GeneralSupport because the target queue has nobody staffed, re-check",
    "  staffing so callers are never sent to an empty queue (requested after INC-30981).",
    "- Pre-deploy checks: JSON schema validation of the flow content passed; no functional changes elsewhere.",
    "",
  ].join("\n"));
  console.log(`bundle written to incident/ (${ctrs.length} contacts, ${logLines.length} flow log lines)`);
}

main();
