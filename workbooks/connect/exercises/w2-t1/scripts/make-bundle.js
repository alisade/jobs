// Generate the incident bundle for connect/w2-t1 into incident/ (deterministic).
// Replays both weeks through the routing model with the configs that were live at the time and
// writes what LFG's monitoring and data lake would hold.
const fs = require("fs");
const path = require("path");
const s = require("../tools/scenario");

const root = path.resolve(__dirname, "..");
const out = path.join(root, "incident");
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(path.join(out, "ctr"), { recursive: true });

const before = { p: require("./routing-profiles-2026-10-02.json"), u: require("./users-2026-10-02.json") };
// the bundle always shows what actually ran in prod that week, whatever is in config/ now
const after = { p: JSON.parse(fs.readFileSync(path.join(__dirname, "prod-2026-10-09.json"), "utf8")), u: require("./users-2026-10-09.json") };

const INSTANCE = "arn:aws:connect:us-east-1:111122223333:instance/5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f";
const iso = (date, sec) => new Date(Date.parse(`${date}T12:00:00Z`) + sec * 1000).toISOString().replace(".000Z", "Z");
const hex = (n, w) => n.toString(16).padStart(w, "0");
const metrics = [["date", "queue", "contacts_queued", "contacts_handled", "contacts_abandoned", "service_level_30s_pct", "avg_queue_answer_time_s", "max_queue_wait_s", "avg_handle_time_s", "agents_staffed"]];
let n = 0;

for (const day of s.DAYS) {
  const cfg = day.phase === "before" ? before : after;
  const r = s.replayDay(cfg.p, cfg.u, day);
  const stream = new Map(s.streamFor(day).map((c) => [c.id, c]));
  const model = s.toModel(cfg.p, cfg.u, day);
  const profileOf = new Map(model.agents.map((a) => [a.id, a.routingProfileId]));
  const lines = [];
  for (const o of r.contacts) {
    const c = stream.get(o.id);
    n++;
    const id = `${hex(0x5e000000 + n, 8)}-${hex(day.seed, 4)}-4c2b-8d1e-${hex(n * 2654435761 % 2 ** 48, 12)}`;
    const enq = o.arrival + 34; // ~34 s in the IVR before the queue
    const deq = o.answeredAt !== null ? o.answeredAt + 34 : o.abandonedAt + 34;
    const rec = {
      AWSAccountId: "111122223333",
      InstanceARN: INSTANCE,
      ContactId: id,
      Channel: "VOICE",
      InitiationMethod: "INBOUND",
      InitiationTimestamp: iso(day.date, o.arrival),
      DisconnectTimestamp: iso(day.date, o.answeredAt !== null ? o.answeredAt + 34 + c.handleSeconds : deq),
      DisconnectReason: o.answeredAt !== null ? "AGENT_DISCONNECT" : "CUSTOMER_DISCONNECT",
      Queue: { Name: s.QUEUES[o.queueId].name, ARN: `${INSTANCE}/queue/${o.queueId}`, EnqueueTimestamp: iso(day.date, enq), DequeueTimestamp: iso(day.date, deq), Duration: deq - enq },
      Agent: o.answeredAt !== null
        ? { Username: o.agentId, ConnectedToAgentTimestamp: iso(day.date, o.answeredAt + 34), AgentInteractionDuration: Math.round(c.handleSeconds * 0.85), AfterContactWorkDuration: Math.round(c.handleSeconds * 0.15), RoutingProfile: { Name: profileOf.get(o.agentId) } }
        : null,
      Attributes: { callerVerified: n % 9 === 0 ? "false" : "true", ivrPath: o.queueId === "q-password-reset" ? "menu-1" : o.queueId === "q-apps" ? "menu-4" : "menu-2" },
    };
    lines.push(JSON.stringify(rec));
  }
  fs.writeFileSync(path.join(out, "ctr", `${day.date}.jsonl`), lines.join("\n") + "\n");
  for (const [q, st] of Object.entries(r.queues)) {
    const handledOnes = r.contacts.filter((o) => o.queueId === q && o.answeredAt !== null);
    const aht = handledOnes.length ? handledOnes.reduce((a, o) => a + stream.get(o.id).handleSeconds, 0) / handledOnes.length : 0;
    const staffed = model.agents.filter((a) => model.routingProfiles.find((p) => p.id === a.routingProfileId).queues.some((x) => x.queueId === q)).length;
    metrics.push([day.date, s.QUEUES[q].name, st.offered, st.handled, st.abandoned, (100 * st.serviceLevel).toFixed(1), st.asaSeconds.toFixed(1), st.maxWaitSeconds, aht.toFixed(0), staffed]);
  }
}
fs.writeFileSync(path.join(out, "historical-metrics.csv"), metrics.map((r) => r.join(",")).join("\n") + "\n");

// Real-time snapshot, Tuesday 2026-10-06 08:56:18 ET (= 12:56:18 UTC, second 3378 of the window)
{
  const day = s.DAYS.find((d) => d.date === "2026-10-06");
  const r = s.replayDay(after.p, after.u, day);
  const stream = new Map(s.streamFor(day).map((c) => [c.id, c]));
  const t = 3378;
  const rows = [];
  for (const q of Object.keys(s.QUEUES)) {
    const waiting = r.contacts.filter((o) => o.queueId === q && o.arrival <= t && ((o.answeredAt ?? o.abandonedAt) > t));
    const oldest = waiting.reduce((m, o) => Math.max(m, t - o.arrival), 0);
    rows.push([s.QUEUES[q].name, waiting.length, oldest]);
  }
  const busy = new Set(r.contacts.filter((o) => o.answeredAt !== null && o.answeredAt <= t && o.answeredAt + stream.get(o.id).handleSeconds > t).map((o) => o.agentId));
  const model = s.toModel(after.p, after.u, day);
  const avail = model.agents.filter((a) => !busy.has(a.id));
  const byProfile = {};
  for (const a of avail) byProfile[a.routingProfileId] = (byProfile[a.routingProfileId] || 0) + 1;
  const txt = [
    "Amazon Connect - Real-time metrics (queues) - exported 2026-10-06 08:56:18 America/New_York",
    "",
    "Queue            In queue  Oldest (s)",
    ...rows.map(([q, w, o]) => `${q.padEnd(16)} ${String(w).padStart(8)}  ${String(o).padStart(10)}`),
    "",
    "Agents Available by routing profile:",
    ...Object.entries(byProfile).map(([p, c]) => `  ${p.padEnd(18)} ${c}`),
    "",
    "(Supervisor note: 'why are people sitting in Available when the board is red?')",
  ];
  fs.writeFileSync(path.join(out, "realtime-snapshot-2026-10-06-0856.txt"), txt.join("\n") + "\n");
}

fs.writeFileSync(path.join(out, "routing-profiles-before-CHG0032015.json"), JSON.stringify(before.p, null, 2) + "\n");
fs.writeFileSync(path.join(out, "routing-profiles-prod-2026-10-09.json"), JSON.stringify(after.p, null, 2) + "\n");
for (const f of ["PAGE.txt", "CHG0032015.txt", "roster-notes.txt"]) fs.copyFileSync(path.join(__dirname, "text", f), path.join(out, f));
console.log(`bundle: ${n} contact records, ${metrics.length - 1} metric rows -> incident/`);
