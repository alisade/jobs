// The LFG Monday-to-Friday 08:00-10:00 ET peak, before and after CHG0032015 (environment).
// Maps the Connect-shaped exports in config/ onto the routing model and replays a day.
const { simulate } = require("./routing-model");
const { generateContacts } = require("./stream");

const QUEUES = {
  "q-password-reset": { name: "PasswordReset", perHour: 140, ahtSeconds: 240, patienceSeconds: 150 },
  "q-general": { name: "GeneralSupport", perHour: 110, ahtSeconds: 480, patienceSeconds: 200 },
  "q-apps": { name: "Applications", perHour: 40, ahtSeconds: 600, patienceSeconds: 260 },
};

// seeds are fixed per day so every replay of a day sees the same callers
const DAYS = [
  { date: "2026-09-28", seed: 1, phase: "before" },
  { date: "2026-09-29", seed: 2, phase: "before" },
  { date: "2026-09-30", seed: 3, phase: "before" },
  { date: "2026-10-01", seed: 4, phase: "before" },
  { date: "2026-10-02", seed: 5, phase: "before" },
  { date: "2026-10-05", seed: 11, phase: "after" },
  { date: "2026-10-06", seed: 12, phase: "after" },
  { date: "2026-10-07", seed: 13, phase: "after", absent: ["gen-03", "gen-07"] }, // CBT training
  { date: "2026-10-08", seed: 14, phase: "after" },
  { date: "2026-10-09", seed: 15, phase: "after" },
];

function streamFor(day) {
  return generateContacts({
    seed: day.seed,
    durationSeconds: 7200,
    queues: Object.entries(QUEUES).map(([queueId, q]) => ({ queueId, perHour: q.perHour, ahtSeconds: q.ahtSeconds, patienceSeconds: q.patienceSeconds })),
  });
}

/** Connect-shaped exports -> routing model config. Throws on references to unknown things. */
function toModel(profilesDoc, usersDoc, day) {
  const queueIds = new Set(Object.keys(QUEUES));
  const routingProfiles = profilesDoc.RoutingProfiles.map((p) => ({
    id: p.Name,
    queues: p.QueueConfigs.filter((c) => c.QueueReference.Channel === "VOICE").map((c) => {
      if (!queueIds.has(c.QueueReference.QueueId)) throw new Error(`${p.Name}: unknown queue ${c.QueueReference.QueueId}`);
      return { queueId: c.QueueReference.QueueId, priority: Number(c.Priority), delaySeconds: Number(c.Delay) };
    }),
  }));
  const absent = new Set((day && day.absent) || []);
  const agents = usersDoc.Users.filter((u) => !absent.has(u.Username)).map((u) => ({ id: u.Username, routingProfileId: u.RoutingProfileName }));
  return { queues: [...queueIds].map((id) => ({ id })), routingProfiles, agents, serviceLevelThresholdSeconds: 30 };
}

function replayDay(profilesDoc, usersDoc, day) {
  return simulate(toModel(profilesDoc, usersDoc, day), streamFor(day));
}

/** Aggregate per-queue figures over a set of days. */
function replayWeek(profilesDoc, usersDoc, phase = "after") {
  const agg = {};
  for (const day of DAYS.filter((d) => d.phase === phase)) {
    const r = replayDay(profilesDoc, usersDoc, day);
    for (const [q, s] of Object.entries(r.queues)) {
      const a = (agg[q] = agg[q] || { offered: 0, handled: 0, abandoned: 0, within: 0, waitSum: 0 });
      a.offered += s.offered;
      a.handled += s.handled;
      a.abandoned += s.abandoned;
      a.within += s.answeredWithinThreshold;
      a.waitSum += s.asaSeconds * s.handled;
    }
  }
  const out = {};
  for (const [q, a] of Object.entries(agg)) {
    out[q] = { offered: a.offered, serviceLevel: a.within / a.offered, abandonRate: a.abandoned / a.offered, asaSeconds: a.handled ? a.waitSum / a.handled : 0 };
  }
  return out;
}

module.exports = { QUEUES, DAYS, streamFor, toModel, replayDay, replayWeek };
