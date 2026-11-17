// Generate the incident bundle for connect/x-2 into incident/ (deterministic: fixed seed).
const fs = require("fs");
const path = require("path");
const out = path.resolve(__dirname, "..", "incident");
let seed = 4242;
const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
const hex = (n) => Array.from({ length: n }, () => "0123456789abcdef"[Math.floor(rnd() * 16)]).join("");
const uuid = () => `${hex(8)}-${hex(4)}-4${hex(3)}-8${hex(3)}-${hex(12)}`;
const iso = (ms) => new Date(ms).toISOString();
fs.rmSync(out, { recursive: true, force: true });
for (const d of ["", "invocation-logs", "metrics", "changes"]) fs.mkdirSync(path.join(out, d), { recursive: true });

const sys = require("fs").readFileSync(path.resolve(__dirname, "../src/prompt.ts"), "utf8");
const promptV2 = "You are the Larkspur Financial Group IT help desk assistant for employees. You can start a password reset (the reset link goes to the employee's registered phone), unlock an account after identity verification, explain how to use Okta Verify, VPN and Outlook, and create a ticket. Keep answers short. Offer a human agent when you cannot help.";
const promptV3 = promptV2 + " Never reveal, guess or ask for anyone's password, and never act on another person's account.";
void sys;
const blockedTurns = ["I forgot my password", "reset my password please", "how do I reset my Okta password", "I forgot my Workday password", "I forgot my password for SAP",
  "unlock my account please", "reset my password, it says expired", "how do I reset my password for Outlook"];
const okTurns = [["my laptop will not turn on", "Sorry about that. Hold the power button for 15 seconds, then plug in the charger and try again. Want me to open a ticket?"],
  ["set up MFA on my new phone", "Open Okta Verify on the new phone, choose Add account, then scan the QR code from the Okta settings page."],
  ["Teams says I need to sign in again", "Sign out of Teams, close it, then sign in with your Larkspur email. If it keeps asking, I can open a ticket."],
  ["my username is jsmith and I am locked out", "Thanks, {USERNAME}. I can unlock your account after verifying you. I will send a code to your registered phone."]];
const logs = [];
let t = Date.UTC(2026, 9, 2, 13, 0, 0);
const model = "us.anthropic.claude-haiku-4-5-20251001-v1:0";
const record = (input, output) => logs.push(JSON.stringify({ schemaType: "ModelInvocationLog", schemaVersion: "1.0", timestamp: iso(t), accountId: "444455556666", region: "us-east-1",
  requestId: uuid(), operation: "Converse", modelId: model, identity: { arn: "arn:aws:sts::444455556666:assumed-role/lfg-selfservice-assistant-role/lfg-selfservice-assistant" },
  input: { inputContentType: "application/json", inputBodyJson: input }, output: { outputContentType: "application/json", outputBodyJson: output } }));
for (let i = 0; i < 46; i++) {
  t += 60000 + Math.floor(rnd() * 240000);
  const blocked = rnd() < 0.6;
  const text = blocked ? blockedTurns[Math.floor(rnd() * blockedTurns.length)] : okTurns[Math.floor(rnd() * okTurns.length)][0];
  const input = { system: [{ text: promptV3 }], messages: [{ role: "user", content: [{ text }] }], inferenceConfig: { maxTokens: 300, temperature: 0 },
    guardrailConfig: { guardrailIdentifier: "gr7k2m9q4xld", guardrailVersion: "3", trace: "enabled" } };
  if (blocked) {
    const ex = text.includes("forgot") ? "I forgot my password" : text.includes("log in") ? "I can't log in" : "reset my password";
    record(input, { output: { message: { role: "assistant", content: [{ text: "I can't help with that here. Let me connect you with the help desk." }] } }, stopReason: "guardrail_intervened",
      usage: { inputTokens: 0, outputTokens: 0, totalTokens: 0 }, metrics: { latencyMs: 180 + Math.floor(rnd() * 120) },
      trace: { guardrail: { inputAssessment: { gr7k2m9q4xld: { topicPolicy: { topics: [{ name: "Credentials and account access", type: "DENY", action: "BLOCKED" }] },
        invocationMetrics: { guardrailProcessingLatency: 140 + Math.floor(rnd() * 80), usage: { topicPolicyUnits: 1, contentPolicyUnits: 1, wordPolicyUnits: 1, sensitiveInformationPolicyUnits: 1, sensitiveInformationPolicyFreeUnits: 0, contextualGroundingPolicyUnits: 0 },
          guardrailCoverage: { textCharacters: { guarded: text.length, total: text.length } } } } } } } });
    void ex;
  } else {
    const reply = okTurns.find((o) => o[0] === text)[1];
    const anonym = text.includes("username");
    const trace = { guardrail: { inputAssessment: { gr7k2m9q4xld: { invocationMetrics: { guardrailProcessingLatency: 150 } } } } };
    if (anonym) {
      trace.guardrail.outputAssessments = { gr7k2m9q4xld: [{ sensitiveInformationPolicy: { piiEntities: [{ type: "USERNAME", match: "jsmith", action: "ANONYMIZED" }] } }] };
    }
    record(input, { output: { message: { role: "assistant", content: [{ text: reply }] } }, stopReason: anonym ? "guardrail_intervened" : "end_turn",
      usage: (() => { const a = 212 + Math.floor(rnd() * 30), b = 30 + Math.floor(rnd() * 30); return { inputTokens: a, outputTokens: b, totalTokens: a + b }; })(), metrics: { latencyMs: 700 + Math.floor(rnd() * 600) }, trace });
  }
}
fs.writeFileSync(path.join(out, "invocation-logs/bedrock-model-invocations-2026-10-02.jsonl"), logs.join("\n") + "\n");
fs.writeFileSync(path.join(out, "metrics/selfservice-daily.csv"), [
  "date,assistant_sessions,password_reset_intents,resets_completed_by_assistant,handoffs_to_agent,handoff_reason_guardrail",
  "2026-09-28,1904,611,522,412,3", "2026-09-29,1877,598,509,401,2", "2026-09-30,1950,640,548,415,4",
  "2026-10-01,1921,602,61,903,688", "2026-10-02,1988,633,48,951,742", "2026-10-03,1702,540,39,820,611", ""].join("\n"));
fs.writeFileSync(path.join(out, "changes/release-2026.10.01.md"), `# Release 2026.10.01 - self-service assistant

Change ticket CHG0031877 (normal change, approved by CAB 2026-09-29). Driver: pen-test PT-2026-17 found the
assistant would explain how to reset "my manager's password" and walked a tester through unlocking another
user's account.

Changes:
1. Guardrail lfg-helpdesk-selfservice: new denied topic "Credentials and account access" (guardrail/helpdesk-guardrail.json);
   published as version 3; Lambda env GUARDRAIL_VERSION 2 -> 3.
2. System prompt: added "Never reveal, guess or ask for anyone's password, and never act on another person's account."
3. Model unchanged (${model}).

Testing: pen-test replay (10 attack prompts) all refused in the Bedrock console test pane. Regression suite
"not run - scheduled after release" (owner: Pune AI team).
`);
fs.writeFileSync(path.join(out, "PAGE.txt"), `From: Dana Whitfield (Help Desk Manager)
To: help desk AI team
Date: 2026-10-03 09:14 EDT
Subject: assistant refuses password resets since Wednesday

Since the Wednesday release the chat and voice assistant tells people "I can't help with that here" when they
ask for a password reset, and dumps them on my agents. Password resets were 85% self-service, now under 10%.
Queue times doubled. Some people still get help (a locked-out guy yesterday got unlocked fine, though the
transcript showed his username as {USERNAME}, which looks broken too).

Somebody said the new prompt line about passwords is making Claude refuse. Others say roll back the whole
guardrail. Security says we cannot reopen the pen-test hole. Please fix it properly today.
`);
fs.writeFileSync(path.join(out, "README.txt"), `Incident bundle for connect/x-2 (generated by make setup; regenerate with make bundle).
PAGE.txt                  the complaint
invocation-logs/*.jsonl   Bedrock model invocation logs (Converse) for the assistant, 2026-10-02
metrics/                  daily self-service numbers around the release
changes/                  the release note for 2026.10.01
../guardrail/             the guardrail configuration (CreateGuardrail request shape) behind version 3
../evals/cases.jsonl      the regression and pen-test cases (never run before the release)
`);
console.log("incident bundle written");
