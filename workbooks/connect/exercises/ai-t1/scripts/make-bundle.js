// Generate the incident bundle for connect/ai-t1 into incident/ (deterministic, no network).
"use strict";
const fs = require("fs");
const path = require("path");

const out = path.resolve(__dirname, "../incident");
let seed = 8102026;
const rand = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
const uuid = () => "xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx".replace(/x/g, () => Math.floor(rand() * 16).toString(16));
const iso = (ms) => new Date(ms).toISOString();
const FN = "arn:aws:lambda:us-east-1:111122223333:function:lfg-contact-summary";
const FLOW = "arn:aws:connect:us-east-1:111122223333:instance/5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f/contact-flow/7d3e9a41-5c2b-4f0e-8a61-0e9b2c4d5f13";

fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });

// 13:00-16:00 ET on 2026-10-08. The analytics backfill job starts 14:02 and shares the account's
// on-demand quota for the same model; throttling follows.
const base = Date.UTC(2026, 9, 8, 17, 0, 0);
const flowLog = [];
const lambdaLog = [];
const traces = [];
let degradedForAgents = 0;
let total = 0;
const durByHour = { 0: [], 1: [], 2: [] };
for (let i = 0; i < 90; i++) {
  const t = base + Math.floor((i * 180 * 60000) / 90) + Math.floor(rand() * 60000);
  const minute = (t - base) / 60000;
  const busy = minute >= 62 && minute < 150;
  const contactId = uuid();
  const reqId = uuid();
  const cold = rand() < 0.06;
  const init = cold ? 410 + Math.floor(rand() * 200) : 0;
  const outTokens = 520 + Math.floor(rand() * 520); // verbose summaries: maxTokens 2048 never binds
  const genMs = 900 + outTokens * 3.1;
  const throttles = busy ? (rand() < 0.75 ? 1 + Math.floor(rand() * 2) : 0) : (rand() < 0.03 ? 1 : 0);
  const attemptsMs = [];
  let delay = 0;
  for (let a = 0; a < throttles; a++) {
    attemptsMs.push({ status: 429, ms: 180 + Math.floor(rand() * 220) });
    delay += 500 * (a + 1) + Math.floor(rand() * 1600 * (a + 1));
  }
  attemptsMs.push({ status: 200, ms: Math.floor(genMs) });
  const duration = init + attemptsMs.reduce((s, x) => s + x.ms, 0) + delay + 40;
  const connectGaveUp = duration > 8000;
  durByHour[Math.min(2, Math.floor(minute / 60))].push(duration - init);
  total++;
  if (connectGaveUp) degradedForAgents++;
  flowLog.push(JSON.stringify({
    Results: connectGaveUp ? "Error" : "Success",
    ContactId: contactId, ContactFlowId: FLOW, ContactFlowName: "LFG Help Desk Inbound",
    ContactFlowModuleType: "InvokeExternalResource", Identifier: "summarize-selfservice",
    Timestamp: iso(t + 8000 * (connectGaveUp ? 1 : duration / 8000)),
    Parameters: { FunctionArn: FN, TimeLimit: "8000", InvocationType: "SYNCHRONOUS" },
    ExternalResults: connectGaveUp ? null : { summaryStatus: "OK", summary: "<redacted in export>" },
  }));
  if (connectGaveUp) {
    flowLog.push(JSON.stringify({ Results: "Success", ContactId: contactId, ContactFlowId: FLOW, ContactFlowName: "LFG Help Desk Inbound", ContactFlowModuleType: "PlayPrompt", Identifier: "summary-unavailable-msg", Timestamp: iso(t + 8100), Parameters: { Text: "Thanks. Connecting you to an analyst now." } }));
  }
  lambdaLog.push(`${iso(t)} START RequestId: ${reqId} Version: 14`);
  if (attemptsMs.length > 1 || connectGaveUp || i % 9 === 0) {
    lambdaLog.push(`${iso(t + duration - 30)}\t${reqId}\tINFO\t${JSON.stringify({ level: "INFO", msg: "converse ok", attempts: attemptsMs.length, totalRetryDelayMs: delay, outputTokens: outTokens, elapsedMs: duration - init - 40 })}`);
  }
  lambdaLog.push(`${iso(t + duration)} END RequestId: ${reqId}`);
  lambdaLog.push(`${iso(t + duration)} REPORT RequestId: ${reqId}\tDuration: ${(duration - init).toFixed(2)} ms\tBilled Duration: ${duration - init + 1} ms\tMemory Size: 256 MB\tMax Memory Used: ${226 + Math.floor(rand() * 22)} MB${cold ? `\tInit Duration: ${init}.37 ms` : ""}`);
  if ((connectGaveUp && traces.length < 4) || (i === 3)) {
    let at = 0;
    const segs = [];
    if (cold) { segs.push(`  Initialization                     ${String(0).padStart(6)} ms  +${init} ms`); at += init; }
    attemptsMs.forEach((a, k) => {
      segs.push(`  bedrock-runtime Converse #${k + 1}       ${String(at).padStart(6)} ms  +${a.ms} ms  HTTP ${a.status}${a.status === 429 ? " ThrottlingException" : ""}`);
      at += a.ms;
      if (k < attemptsMs.length - 1) {
        const back = Math.floor(delay / throttles);
        segs.push(`  (SDK retry backoff)                ${String(at).padStart(6)} ms  +${back} ms`);
        at += back;
      }
    });
    traces.push([`trace 1-${uuid().slice(0, 8)}  ${iso(t)}  lfg-contact-summary  total ${duration} ms  contact ${contactId}`, ...segs, `  Connect waited until 8000 ms -> ${connectGaveUp ? "Error branch" : "Success"}`, ""].join("\n"));
  }
}
const pct = (a, q) => { const b = a.slice().sort((x, y) => x - y); return Math.round(b[Math.min(b.length - 1, Math.floor(q * b.length))] || 0); };
fs.writeFileSync(path.join(out, "flow-logs-2026-10-08.log"), flowLog.join("\n") + "\n");
fs.writeFileSync(path.join(out, "lambda-lfg-contact-summary-2026-10-08.log"), lambdaLog.join("\n") + "\n");
fs.writeFileSync(path.join(out, "trace-samples.txt"), "X-Ray style segment timelines (exported from the console, abbreviated)\n\n" + traces.join("\n"));
fs.writeFileSync(path.join(out, "metrics-2026-10-08.txt"), [
  "AWS/Lambda  FunctionName=lfg-contact-summary   (hourly, local time)",
  "                         13:00    14:00    15:00",
  "Invocations                 30       30       30",
  "Errors                       0        0        0",
  "Throttles                    0        0        0",
  "Duration p50 (ms)      " + [0, 1, 2].map((h) => String(pct(durByHour[h], 0.5)).padStart(9)).join(""),
  "Duration max (ms)      " + [0, 1, 2].map((h) => String(pct(durByHour[h], 1)).padStart(9)).join(""),
  "ConcurrentExecutions max     2        4        2",
  "",
  "AWS/Bedrock  ModelId=us.anthropic.claude-haiku-4-5-20251001-v1:0   (all callers in account 111122223333)",
  "Invocations                 31     1874     1210",
  "InvocationThrottles          0      412      198",
  "InvocationLatency p50 (ms) 2810     2950     2890",
  "OutputTokenCount sum     23410   689001   421877",
  "",
  `Connect: ${degradedForAgents} of ${total} sampled contacts took the summarize-selfservice Error branch (flow logs).`,
  "",
].join("\n"));
fs.writeFileSync(path.join(out, "PAGE.txt"), [
  "ServiceNow INC0102231  P3  opened 2026-10-08 15:12 ET by Dana (Service desk lead, Charlotte)",
  "Short description: Agent screen pop missing the AI summary for many calls this afternoon",
  "",
  "Since about 2 PM roughly one call in five arrives without the self-service summary in the agent panel, so",
  "analysts re-ask every question. Callers also hear 8 seconds of silence before 'Connecting you to an analyst'.",
  "",
  "Work notes:",
  "15:20 Ravi (Pune, L2): Lambda lfg-contact-summary shows 0 errors and 0 throttles in CloudWatch. The function",
  "      completes fine, some runs take 8-10 s. Max Memory Used is 245 MB of 256 MB - we should raise memory to",
  "      1024 MB, that will make it faster.",
  "15:31 Priya (Analytics): unrelated, but we kicked off the CTR summarization backfill (lfg-ctr-summarizer-backfill)",
  "      at 14:02 in the same account; it runs until about 15:30.",
  "15:40 You (Connect lead) are assigned. config/lambda.json is the deployed function configuration.",
  "",
].join("\n"));
console.log(`bundle written to incident/ (${total} invocations, ${degradedForAgents} hit Connect's 8 s limit)`);
