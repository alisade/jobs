// Generate the incident bundle for connect/w7-t1 into incident/ (deterministic).
// Flow logs and contact records are produced by running THIS checkout's flows and module through the
// connect-kit interpreter, so after a fix `make bundle` shows the fixed behavior.
const fs = require("fs");
const path = require("path");
const k = require("connect-kit");

const root = path.resolve(__dirname, "..");
const out = path.join(root, "incident");
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });
const load = (p) => JSON.parse(fs.readFileSync(path.join(root, p), "utf8"));
const res = load("config/resources.json");
const flows = { VOICE: load("flows/helpdesk-voice-inbound.json"), CHAT: load("flows/helpdesk-chat-inbound.json") };
const modules = { [res.modules["lfg-handoff"]]: load("modules/lfg-handoff.json") };
const INST = "arn:aws:connect:us-east-1:111122223333:instance/5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f";
const flowIds = { VOICE: "cf-voice-0141", CHAT: "cf-chat-0012" };
const LOGTYPE = {
  UpdateFlowLoggingBehavior: "SetLoggingBehavior", ConnectParticipantWithLexBot: "GetUserInput", UpdateContactAttributes: "SetAttributes",
  InvokeFlowModule: "InvokeFlowModule", Compare: "CheckAttribute", UpdateContactTargetQueue: "SetQueue", TransferContactToQueue: "Transfer",
  MessageParticipant: "PlayPrompt", DisconnectParticipant: "Disconnect", EndFlowModuleExecution: "Return",
};

const contacts = [
  { id: "0b6d1f0e-2a51-4c7e-9a0f-6e2d55a10001", ch: "VOICE", at: "2026-10-07T14:02:11Z", intent: "ResetPassword", summary: "Locked out after replacing phone; needs password reset and MFA re-registration.", slots: { device: "new phone", accountType: "standard" }, utter: "I got a new phone and now I cannot sign in" },
  { id: "0b6d1f0e-2a51-4c7e-9a0f-6e2d55a10002", ch: "CHAT", at: "2026-10-07T14:05:40Z", intent: "ResetPassword", summary: "Password expired while travelling; portal reset fails at MFA step.", slots: { device: "laptop", accountType: "standard" }, utter: "my password expired and the reset page keeps asking for a code I do not get", initial: "9f3e7a10-55c2-4b1d-8e0a-1c2d3e4f0002" },
  { id: "0b6d1f0e-2a51-4c7e-9a0f-6e2d55a10003", ch: "CHAT", at: "2026-10-07T14:11:03Z", intent: "VpnIssue", summary: "GlobalProtect disconnects every 10 minutes since Monday.", slots: { client: "GlobalProtect" }, utter: "vpn keeps dropping" },
  { id: "0b6d1f0e-2a51-4c7e-9a0f-6e2d55a10004", ch: "VOICE", at: "2026-10-07T14:15:52Z", intent: "VpnIssue", summary: "VPN will not connect from hotel Wi-Fi.", slots: { client: "GlobalProtect" }, utter: "the vpn will not connect" },
  { id: "0b6d1f0e-2a51-4c7e-9a0f-6e2d55a10005", ch: "CHAT", at: "2026-10-07T14:20:18Z", intent: "Escalate", summary: "Asked for a human after two failed attempts to describe a Teams audio issue.", slots: {}, utter: "agent please" },
];

const flowLog = [];
const ctrs = [];
const lexLog = [];
let t0 = 0;
for (const c of contacts) {
  const sessionAttributes = { botSummary: c.summary, lexSlots: JSON.stringify(c.slots), callerVerified: "true", channel: c.ch };
  const r = k.simulate(flows[c.ch], { channel: c.ch, contactId: c.id, lex: [{ intent: c.intent, slots: c.slots, sessionAttributes }], modules });
  const base = Date.parse(c.at);
  r.trace.forEach((s, i) => {
    const a = (s.module ? modules[res.modules["lfg-handoff"]] : flows[c.ch]).Actions.find((x) => x.Identifier === s.id) || { Parameters: {} };
    const entry = {
      ContactId: c.id,
      ContactFlowId: `${INST}/contact-flow/${s.module ? "mod-lfg-handoff" : flowIds[c.ch]}`,
      ContactFlowName: s.module ? "lfg-handoff (module)" : flows[c.ch].Metadata.name,
      ContactFlowModuleType: LOGTYPE[s.type] || s.type,
      Identifier: s.id,
      Timestamp: new Date(base + i * 900).toISOString(),
      Parameters: a.Type === "UpdateContactAttributes" ? Object.fromEntries(Object.keys(a.Parameters.Attributes).map((key) => [key, (r.attributes[key] ?? "")])) : a.Type === "ConnectParticipantWithLexBot" ? { BotAliasArn: res.lexBotAlias } : {},
      ...(s.type === "ConnectParticipantWithLexBot" ? { Results: c.intent } : {}),
    };
    flowLog.push(entry);
  });
  lexLog.push({
    messageVersion: "2.0",
    bot: { name: "LFG-HelpDesk", version: "7", localeId: "en_US", id: "HDBOT01", aliasId: "PROD01", aliasName: "prod" },
    sessionId: c.id,
    inputMode: c.ch === "VOICE" ? "Speech" : "Text",
    inputTranscript: c.utter,
    interpretations: [{ intent: { name: c.intent, state: "ReadyForFulfillment" }, nluConfidence: 0.91 }],
    sessionState: { intent: { name: c.intent, state: "ReadyForFulfillment", slots: Object.fromEntries(Object.entries(c.slots).map(([s, v]) => [s, { value: { originalValue: v, interpretedValue: v } }])) }, sessionAttributes },
    timestamp: new Date(base + 1500).toISOString(),
  });
  const qName = (r.queue || "").endsWith("q-password-reset") ? "PasswordReset" : "GeneralSupport";
  ctrs.push({
    ContactId: c.id,
    InitialContactId: c.initial || c.id,
    ...(c.initial ? { RelatedContactId: c.initial } : {}),
    Channel: c.ch,
    InitiationMethod: c.ch === "VOICE" ? "INBOUND" : "API",
    InitiationTimestamp: c.at,
    Queue: { Name: qName, ARN: r.queue },
    Agent: { Username: ["aisha.k", "bruno.m", "chen.l"][t0++ % 3] },
    Attributes: r.attributes,
    ...(c.ch === "CHAT" ? { ChatMetrics: { ConversationCloseReason: "CUSTOMER_DISCONNECT" } } : {}),
  });
}

const w = (name, body) => fs.writeFileSync(path.join(out, name), body);
w("PAGE.txt", `INC0047311  P3  opened 2026-10-07 15:02 by Rosa Delgado (Help desk team lead, Monterrey)

Since yesterday's release, CHAT agents say the "Help desk assistant" panel is blank when the bot hands a
chat over: no summary, no intent, no slots, "Caller not verified" warning on every chat. Voice is fine.
Agents are re-asking everything; chat AHT is up 2m40s since yesterday. The bot itself seems fine:
customers say they explained everything to it. Offshore dev (Pune) says the agent app did not change.

Thread:
 15:10 Priya (Pune dev): app unchanged since 2026-09-22. Chats have a different InitialContactId than
       ContactId in the CTR (persistent chat?). Maybe the app reads attributes from the wrong contact?
 15:14 Marco (Connect admin): release 2026.10.06 only touched flows. Lex bot version unchanged (7).
 15:20 Rosa: can someone look today? Monday 8am is our chat peak.
`);
w("release-2026.10.06.md", `# Release 2026.10.06 (Connect flows)

- refactor: new shared flow module \`lfg-handoff\` (copies bot context into contact attributes before
  transfer). Adopted by Chat Inbound v12; Voice Inbound to adopt next sprint.
- Chat Inbound v12: replaced the inline "Set contact attributes" block with "Invoke module lfg-handoff".
- Lex bot LFG-HelpDesk: no change (alias prod -> version 7).
- Agent app: no change.
Tested: chat reaches the right queue for ResetPassword and VpnIssue in UAT.
`);
w("flow-logs.jsonl", flowLog.map((x) => JSON.stringify(x)).join("\n") + "\n");
w("lex-conversation-logs.jsonl", lexLog.map((x) => JSON.stringify(x)).join("\n") + "\n");
w("contact-records.jsonl", ctrs.map((x) => JSON.stringify(x)).join("\n") + "\n");
const chat = ctrs.find((x) => x.Channel === "CHAT");
const voice = ctrs.find((x) => x.Channel === "VOICE");
const panel = (c) => `Contact ${c.ContactId} (${c.Channel.toLowerCase()})
  Handoff from bot (${c.Channel.toLowerCase()})
  ${c.Attributes.callerVerified === "true" ? "" : "[!] Caller not verified: complete identity verification first.\n  "}Summary: ${c.Attributes.botSummary || "No bot summary"}
  Intent: ${c.Attributes.lexIntent || "unknown"}
  Slots: ${c.Attributes.lexSlots || "(none)"}
`;
w("agent-workspace-screens.txt", `Text captures of the Help desk assistant panel (2026-10-07)\n\n${panel(voice)}\n${panel(chat)}`);
console.log(`incident bundle written to ${path.relative(process.cwd(), out) || "incident"}/ (${contacts.length} contacts)`);
