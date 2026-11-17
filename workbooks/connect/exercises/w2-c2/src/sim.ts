// Routing simulator for the LFG help desk design.
//
// The routing team's first cut: FIFO across everything, first free agent wins. It ignores
// routing-profile priority and delay, contact priority, routing criteria and abandons, and
// its metrics are approximate. Rewrite it to the semantics in README.md; keep the exports.
import { Agent, AgentStats, Contact, ContactOutcome, CriteriaStep, QueueStats, SimConfig, SimReport } from "./types";

/** The routing-criteria step active after waiting `wait` seconds; null when all have expired. */
export function activeStep(steps: CriteriaStep[], wait: number): CriteriaStep | null {
  // TODO
  return steps[0] || null;
}

/** Does the agent satisfy every condition of the step (null step = anyone)? */
export function agentMatches(agent: Agent, step: CriteriaStep | null): boolean {
  // TODO
  return true;
}

export function simulate(config: SimConfig, contacts: Contact[]): SimReport {
  const queue = contacts.slice().sort((a, b) => a.arrival - b.arrival);
  const busyUntil = new Map<string, number>(config.agents.map((a) => [a.id, 0]));
  const handled = new Map<string, number>(config.agents.map((a) => [a.id, 0]));
  const busy = new Map<string, number>(config.agents.map((a) => [a.id, 0]));
  const outs: ContactOutcome[] = [];
  let horizon = 0;
  for (const c of queue) {
    // first agent (config order) whose profile has the queue; wait until it is free
    const cands = config.agents.filter((a) => config.routingProfiles.find((p) => p.id === a.routingProfileId)!.queues.some((q) => q.queueId === c.queueId));
    if (!cands.length) {
      outs.push({ id: c.id, queueId: c.queueId, arrival: c.arrival, answeredAt: null, agentId: null, abandonedAt: c.arrival, waitSeconds: 0 });
      continue;
    }
    const a = cands.reduce((m, x) => (busyUntil.get(x.id)! < busyUntil.get(m.id)! ? x : m), cands[0]);
    const start = Math.max(c.arrival, busyUntil.get(a.id)!);
    busyUntil.set(a.id, start + c.handleSeconds);
    handled.set(a.id, handled.get(a.id)! + 1);
    busy.set(a.id, busy.get(a.id)! + c.handleSeconds);
    horizon = Math.max(horizon, start + c.handleSeconds);
    outs.push({ id: c.id, queueId: c.queueId, arrival: c.arrival, answeredAt: start, agentId: a.id, abandonedAt: null, waitSeconds: start - c.arrival });
  }
  const stats = (os: ContactOutcome[]): QueueStats => {
    const h = os.filter((o) => o.answeredAt !== null);
    const within = h.filter((o) => o.waitSeconds < config.serviceLevelThresholdSeconds).length;
    return {
      offered: os.length,
      handled: h.length,
      abandoned: os.length - h.length,
      answeredWithinThreshold: within,
      serviceLevel: h.length ? within / h.length : 1, // TODO: is this the right denominator?
      asaSeconds: h.length ? h.reduce((s, o) => s + o.waitSeconds, 0) / h.length : 0,
      maxWaitSeconds: os.reduce((m, o) => Math.max(m, o.waitSeconds), 0),
      abandonRate: os.length ? (os.length - h.length) / os.length : 0,
    };
  };
  const queues: Record<string, QueueStats> = {};
  for (const q of config.queues) queues[q.id] = stats(outs.filter((o) => o.queueId === q.id));
  const agents: Record<string, AgentStats> = {};
  for (const a of config.agents) agents[a.id] = { handled: handled.get(a.id)!, busySeconds: busy.get(a.id)!, occupancy: busy.get(a.id)! / Math.max(horizon, 1) };
  return { horizon, queues, agents, overall: stats(outs), contacts: outs };
}
