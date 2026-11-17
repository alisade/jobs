// Generate the incident bundle for connect/x-3 into incident/ (deterministic: fixed seed).
// Conversation logs are produced by the offline NLU over the two DEPLOYED bot versions kept in
// scripts/fixtures/ (version 7 before the release, version 8 after), so the bundle does not depend on your fix.
const fs = require("fs");
const path = require("path");
const ts = require("typescript");
require.extensions[".ts"] = (m, file) => {
  m._compile(ts.transpileModule(fs.readFileSync(file, "utf8"), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true } }).outputText, file);
};
const { loadBot, recognize } = require("../tools/nlu.ts");
const root = path.resolve(__dirname, "..");
const out = path.join(root, "incident");
let seed = 99173;
const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
const pick = (a) => a[Math.floor(rnd() * a.length)];
const hex = (n) => Array.from({ length: n }, () => "0123456789abcdef"[Math.floor(rnd() * 16)]).join("");
const uuid = () => `${hex(8)}-${hex(4)}-4${hex(3)}-8${hex(3)}-${hex(12)}`;
const iso = (ms) => new Date(ms).toISOString();
fs.rmSync(out, { recursive: true, force: true });
for (const d of ["", "conversation-logs", "analytics", "changes"]) fs.mkdirSync(path.join(out, d), { recursive: true });

const v7 = loadBot(path.join(root, "scripts/fixtures/bot-version-7/HelpDeskBot"));
const v8 = loadBot(path.join(root, "scripts/fixtures/bot-version-8/HelpDeskBot"));
const said = ["reset my okta password", "i forgot my workday password", "my outlook password expired", "reset my email password", "unlock my sap account",
  "i am locked out of workday", "vpn is down", "is outlook down", "globalprotect is not working for anyone", "remote access is down", "i forgot my password",
  "check my ticket", "what is the status of my ticket", "my single sign on account is locked", "email is down", "is workday down", "reset my sap password",
  "locked out", "i need a new okta password", "sap is down"];
function logs(bot, version, day, n) {
  const lines = [];
  let t = day;
  for (let i = 0; i < n; i++) {
    t += 40000 + Math.floor(rnd() * 200000);
    const u = pick(said);
    const r = recognize(bot, u);
    const slots = {};
    for (const [k, v] of Object.entries(r.slots)) slots[k] = v ? { value: { originalValue: v.originalValue, interpretedValue: v.interpretedValue, resolvedValues: [v.interpretedValue] } } : null;
    lines.push(JSON.stringify({
      timestamp: iso(t), requestId: uuid(), sessionId: uuid(), operationName: "RecognizeUtterance", inputMode: "Speech",
      bot: { name: "HelpDeskBot", version: String(version), localeId: "en_US", aliasName: "live", aliasId: "TSTLIVE001" },
      inputTranscript: u, missedUtterance: r.intent === "FallbackIntent",
      interpretations: [r.intent === "FallbackIntent" ? { interpretationSource: "Lex", intent: { name: "FallbackIntent", slots: {}, state: "ReadyForFulfillment", confirmationState: "None" } } : null,
        ...r.alternatives.filter((a) => a.intent !== r.intent).slice(0, 2).map((a) => ({ interpretationSource: "Lex", nluConfidence: a.confidence, intent: { name: a.intent, slots: {}, state: "InProgress", confirmationState: "None" } }))]
        .filter(Boolean).concat(r.intent === "FallbackIntent" ? [] : [{ interpretationSource: "Lex", nluConfidence: r.confidence, intent: { name: r.intent, slots, state: "InProgress", confirmationState: "None" } }])
        .sort((a, b) => (b.nluConfidence || 0) - (a.nluConfidence || 0)),
      sessionState: { intent: { name: r.intent, slots, state: r.intent === "FallbackIntent" ? "ReadyForFulfillment" : "InProgress", confirmationState: "None" },
        dialogAction: r.intent !== "FallbackIntent" && Object.keys(r.slots).length && !r.slots.System ? { type: "ElicitSlot", slotToElicit: "System" } : { type: r.intent === "FallbackIntent" ? "Close" : "Delegate" } },
    }));
  }
  return lines;
}
fs.writeFileSync(path.join(out, "conversation-logs/HelpDeskBot-live-2026-10-04.jsonl"), logs(v7, 7, Date.UTC(2026, 9, 4, 13, 0, 0), 60).join("\n") + "\n");
fs.writeFileSync(path.join(out, "conversation-logs/HelpDeskBot-live-2026-10-06.jsonl"), logs(v8, 8, Date.UTC(2026, 9, 6, 13, 0, 0), 60).join("\n") + "\n");
fs.writeFileSync(path.join(out, "analytics/daily.csv"), [
  "date,bot_version,utterances,missed_utterances,fallback_rate,system_slot_elicitations,system_slot_elicitation_failures,transfers_to_agent",
  "2026-10-02,7,4120,151,3.7%,212,19,880", "2026-10-03,7,3988,149,3.7%,204,22,861", "2026-10-04,7,2140,83,3.9%,118,9,455",
  "2026-10-05,8,1902,402,21.1%,1544,1201,903", "2026-10-06,8,4210,961,22.8%,3398,2711,2240", "2026-10-07,8,4033,912,22.6%,3301,2633,2187", ""].join("\n"));
fs.writeFileSync(path.join(out, "changes/bot-version-8.md"), `# HelpDeskBot version 8 (alias live moved 7 -> 8 on 2026-10-05 01:10 EDT)

Change CHG0031902, owner: Pune conversational AI team.

1. CMDB alignment (ITSM request RITM0088120): the ServiceNow integration needs the CMDB configuration item
   code in cmdb_ci. The SystemName slot type values were replaced by the CI codes from the CMDB export
   (CI-OKTA-PROD, CI-WORKDAY, CI-SAP-ECC, CI-EXCHANGE-ONLINE, CI-GLOBALPROTECT); value selection set to
   "original value" so the code is passed through unchanged.
2. Voice: Joanna (neural) -> Ruth (generative) for a warmer greeting, per CX feedback.
3. No intent or utterance changes. Confidence threshold unchanged (0.40).

Validation: bot built successfully; test workbench run against the 2026-09 test set skipped (test set
"still references old values").
Suggested by on-call 2026-10-06: lower nluConfidenceThreshold to 0.25 to stop the fallbacks.
`);
fs.writeFileSync(path.join(out, "PAGE.txt"), `Supervisor escalation, 2026-10-07 10:20 EDT

Since Monday the bot keeps saying "Sorry, I didn't get that" or asking "Which system is this about?" over and
over. People say "VPN is down" and get transferred to a general agent with no context. Transfers to agents
more than doubled. The voice change was the only thing we noticed (new voice sounds nice, though).

On-call thinks the new generative voice is slower and callers talk over it, and wants to lower the
confidence threshold to 0.25 as a quick fix. The ServiceNow team says DO NOT go back to the old values:
their integration needs the CI codes.
`);
fs.writeFileSync(path.join(out, "README.txt"), `Incident bundle for connect/x-3 (generated by make setup; regenerate with make bundle).
PAGE.txt                    the escalation
conversation-logs/*.jsonl   Lex conversation logs for the live alias, before (version 7) and after (version 8)
analytics/daily.csv         daily bot analytics around the change
changes/bot-version-8.md    the release note
../scripts/fixtures/        the two deployed bot versions (Lex JSON export) for diffing
../bot/HelpDeskBot/         the bot definition you fix (same as version 8)
`);
console.log("incident bundle written");
