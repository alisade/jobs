// Generate the incident bundle for connect/x-1 into incident/ (deterministic: fixed seed).
const fs = require("fs");
const path = require("path");
const out = path.resolve(__dirname, "..", "incident");
let seed = 77031;
const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
const hex = (n) => Array.from({ length: n }, () => "0123456789abcdef"[Math.floor(rnd() * 16)]).join("");
const uuid = () => `${hex(8)}-${hex(4)}-4${hex(3)}-8${hex(3)}-${hex(12)}`;
const iso = (ms) => new Date(ms).toISOString();
const snTime = (ms) => iso(ms).replace("T", " ").slice(0, 19);
fs.rmSync(out, { recursive: true, force: true });
for (const d of ["", "lambda-logs", "servicenow", "flow-logs", "traces"]) fs.mkdirSync(path.join(out, d), { recursive: true });

const issues = ["Cannot connect to GlobalProtect VPN", "Outlook keeps asking for password", "Laptop docking station no display",
  "Workday login loop", "SAP GUI crashes on launch", "Teams audio not working", "Okta Verify push not arriving", "Printer on 7th floor offline"];
const people = ["E10442", "E10917", "E11208", "E11930", "E12011", "E12577", "E13004", "E13350", "E13871", "E14102", "E14550", "E15013"];
let incNo = 12000;
const lambda = [], snRows = [], flow = [], traces = [];
const day = Date.UTC(2026, 9, 8, 12, 0, 0); // 08:00 EDT
let t = day;
let dupes = 0, contacts = 0;
while (t < day + 10 * 3600 * 1000) {
  const hourEdt = Math.floor((t - day) / 3600000) + 8;
  const peak = hourEdt === 9 || hourEdt === 10 || hourEdt === 13;
  t += (peak ? 25 : 70) * 1000 + Math.floor(rnd() * 40000);
  contacts++;
  const cid = uuid();
  const rid = uuid();
  const emp = people[Math.floor(rnd() * people.length)];
  const issue = issues[Math.floor(rnd() * issues.length)];
  const snLatency = peak ? 1900 + Math.floor(rnd() * 1500) : 350 + Math.floor(rnd() * 500);
  const timedOut = snLatency > 2500;
  flow.push(JSON.stringify({ ContactId: cid, ContactFlowName: "LFG Help Desk Inbound", ContactFlowModuleType: "InvokeExternalResource", Identifier: "create-incident", Timestamp: iso(t), Parameters: { FunctionArn: "arn:aws:lambda:us-east-1:444455556666:function:lfg-create-incident:live", TimeLimit: "8000" }, Results: "Success" }));
  lambda.push(`${iso(t + 20)} START RequestId: ${rid} Version: 17`);
  lambda.push(`${iso(t + 25)} ${rid} INFO contact=${cid} employee=${emp} category=${issue.includes("VPN") ? "network" : "software"} creating incident`);
  let end;
  if (!timedOut) {
    incNo++;
    snRows.push([`INC00${incNo}`, snTime(t + 30 + snLatency - 40), cid, emp, issue, "connect.integration"]);
    lambda.push(`${iso(t + 30 + snLatency)} ${rid} INFO POST /api/now/table/incident attempt=1 status=201 ms=${snLatency} number=INC00${incNo}`);
    end = t + 40 + snLatency;
    traces.push(`${iso(t)} contact=${cid} lambda=${end - t}ms  [POST incident ${snLatency}ms 201]`);
  } else {
    dupes++;
    incNo++;
    const first = `INC00${incNo}`;
    snRows.push([first, snTime(t + 30 + snLatency - 40), cid, emp, issue, "connect.integration"]);
    lambda.push(`${iso(t + 2531)} ${rid} WARN POST /api/now/table/incident attempt=1 failed: network/timeout: AbortError after 2501 ms; retrying in 200 ms`);
    const second = 600 + Math.floor(rnd() * 900);
    incNo++;
    snRows.push([`INC00${incNo}`, snTime(t + 2731 + second - 40), cid, emp, issue, "connect.integration"]);
    lambda.push(`${iso(t + 2731 + second)} ${rid} INFO POST /api/now/table/incident attempt=2 status=201 ms=${second} number=INC00${incNo}`);
    end = t + 2741 + second;
    traces.push(`${iso(t)} contact=${cid} lambda=${end - t}ms  [POST incident 2501ms ABORTED (server finished at ${snLatency}ms -> ${first})] [sleep 200ms] [POST incident ${second}ms 201 -> INC00${incNo}]`);
  }
  lambda.push(`${iso(end)} END RequestId: ${rid}`);
  lambda.push(`${iso(end)} REPORT RequestId: ${rid} Duration: ${end - t - 20}.00 ms Billed Duration: ${end - t - 20} ms Memory Size: 256 MB Max Memory Used: 92 MB`);
}
fs.writeFileSync(path.join(out, "lambda-logs/lfg-create-incident-2026-10-08.log"), lambda.join("\n") + "\n");
fs.writeFileSync(path.join(out, "flow-logs/create-incident-block-2026-10-08.jsonl"), flow.join("\n") + "\n");
fs.writeFileSync(path.join(out, "traces/request-timings-2026-10-08.txt"),
  "Per-contact timing of lfg-create-incident (from X-Ray subsegments, summarized). ServiceNow server time is taken from\n" +
  "the ServiceNow transaction log for the matching POST.\n\n" + traces.join("\n") + "\n");
fs.writeFileSync(path.join(out, "servicenow/incident-export-2026-10-08.csv"),
  "number,sys_created_on,correlation_id,caller_id.user_name,short_description,sys_created_by\n" +
  snRows.map((r) => r.map((x) => (String(x).includes(",") ? `"${x}"` : x)).join(",")).join("\n") + "\n");
// ServiceNow transaction log summary (response time by hour for the integration user)
const lines = ["hour_edt,transactions,p50_ms,p95_ms,max_ms   (POST /api/now/table/incident, user connect.integration)"];
for (let h = 8; h < 18; h++) {
  const peak = h === 9 || h === 10 || h === 13;
  lines.push(`${String(h).padStart(2, "0")}:00,${peak ? 140 : 52},${peak ? 2280 : 610},${peak ? 3240 : 940},${peak ? 3790 : 1310}`);
}
lines.push("", "Note from the ServiceNow admin (2026-10-07): business rule 'LFG - Assignment group lookup (sync)' was",
  "changed on 2026-10-05 to call the CMDB relationship API synchronously on insert. Average insert time went up.");
fs.writeFileSync(path.join(out, "servicenow/transaction-times-2026-10-08.txt"), lines.join("\n") + "\n");
fs.writeFileSync(path.join(out, "PAGE.txt"), `ServiceNow problem PRB0040117 (raised by Service Desk QA, 2026-10-08 18:12 EDT)
Title: Duplicate incidents from phone channel

Since Monday the Service Desk sees pairs of identical incidents created by connect.integration for the
same call: same caller, same short description, created a few seconds apart. Agents work one and the
other breaches its SLA. Today: ${dupes} pairs out of ${contacts} phone incidents. It does not happen every call and
"seems worse in the morning".

Thread
- Integration on-call: "Connect must be invoking the Lambda twice. Connect retries Lambdas that fail,
  and the flow team changed the inbound flow last week. Can we add a dedupe business rule in ServiceNow
  that deletes the second one?"
- Flow team: "We did not touch the create-incident block."
- ServiceNow admin: "Nothing changed on our side except a business rule tweak."

You own the Lambda (src/). Find the cause, fix it in the Lambda, write it up.
`);
fs.writeFileSync(path.join(out, "README.txt"), `Incident bundle for connect/x-1 (generated by make setup; regenerate with make bundle).
PAGE.txt                       the problem record and the thread
lambda-logs/*.log              lfg-create-incident logs for 2026-10-08 (prod, release 2026.08.3)
flow-logs/*.jsonl              Connect flow log lines for the create-incident block, one per contact
servicenow/incident-export*.csv  incidents created by connect.integration that day
servicenow/transaction-times*  ServiceNow response times for the integration's POSTs, and an admin note
traces/                        per-contact timing summary (X-Ray), with the ServiceNow server time
../config/lambda.env           the Lambda's prod configuration
`);
console.log(`incident bundle written (${dupes} duplicate pairs / ${contacts} contacts)`);
