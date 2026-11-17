// LFG routing model (environment, not the suspect): a deterministic model of Connect routing
// semantics (profile priority and delay, contact priority, proficiency steps, abandons).
// Treat it like the Connect runtime: read it if you want, do not change it.
Object.defineProperty(exports, "__esModule", { value: true });
exports.activeStep = activeStep;
exports.agentMatches = agentMatches;
exports.simulate = simulate;
const DEFAULT_PRIORITY = 5;
/** The routing-criteria step active after waiting `wait` seconds; null when all have expired. */
function activeStep(steps, wait) {
    let elapsed = 0;
    for (const s of steps) {
        if (s.expirySeconds === undefined)
            return s;
        if (wait < elapsed + s.expirySeconds)
            return s;
        elapsed += s.expirySeconds;
    }
    return null;
}
function agentMatches(agent, step) {
    if (!step)
        return true;
    const prof = agent.proficiencies || [];
    return step.conditions.every((c) => prof.some((p) => p.attribute === c.attribute && p.value === c.value && p.level >= c.minLevel));
}
function validate(config, contacts) {
    const queues = new Set(config.queues.map((q) => q.id));
    const profiles = new Map(config.routingProfiles.map((p) => [p.id, p]));
    for (const p of config.routingProfiles) {
        for (const q of p.queues) {
            if (!queues.has(q.queueId))
                throw new Error(`routing profile ${p.id} references unknown queue ${q.queueId}`);
            if (q.delaySeconds < 0)
                throw new Error(`routing profile ${p.id}: delay must be >= 0`);
        }
    }
    for (const a of config.agents)
        if (!profiles.has(a.routingProfileId))
            throw new Error(`agent ${a.id} has unknown routing profile ${a.routingProfileId}`);
    const ids = new Set();
    for (const c of contacts) {
        if (!queues.has(c.queueId))
            throw new Error(`contact ${c.id} targets unknown queue ${c.queueId}`);
        if (ids.has(c.id))
            throw new Error(`duplicate contact id ${c.id}`);
        ids.add(c.id);
        if (!Number.isInteger(c.arrival) || c.arrival < 0)
            throw new Error(`contact ${c.id}: arrival must be a non-negative integer`);
        if (!Number.isInteger(c.handleSeconds) || c.handleSeconds < 1)
            throw new Error(`contact ${c.id}: handleSeconds must be an integer >= 1`);
    }
}
function emptyStats() {
    return { offered: 0, handled: 0, abandoned: 0, answeredWithinThreshold: 0, serviceLevel: 1, asaSeconds: 0, maxWaitSeconds: 0, abandonRate: 0 };
}
function summarize(outcomes, threshold) {
    const s = emptyStats();
    let waitSum = 0;
    for (const o of outcomes) {
        s.offered++;
        s.maxWaitSeconds = Math.max(s.maxWaitSeconds, o.waitSeconds);
        if (o.answeredAt !== null) {
            s.handled++;
            waitSum += o.waitSeconds;
            if (o.waitSeconds <= threshold)
                s.answeredWithinThreshold++;
        }
        else
            s.abandoned++;
    }
    s.serviceLevel = s.offered ? s.answeredWithinThreshold / s.offered : 1;
    s.asaSeconds = s.handled ? waitSum / s.handled : 0;
    s.abandonRate = s.offered ? s.abandoned / s.offered : 0;
    return s;
}
function simulate(config, contacts) {
    validate(config, contacts);
    const profiles = new Map(config.routingProfiles.map((p) => [p.id, p]));
    const pending = contacts.slice().sort((a, b) => a.arrival - b.arrival || (a.id < b.id ? -1 : 1));
    const waiting = [];
    const outcome = new Map();
    for (const c of contacts) {
        outcome.set(c.id, { id: c.id, queueId: c.queueId, arrival: c.arrival, answeredAt: null, agentId: null, abandonedAt: null, waitSeconds: 0 });
    }
    const agents = config.agents.map((a) => ({ agent: a, busyUntil: 0, idleSince: 0, handled: 0, busySeconds: 0 }));
    let next = 0;
    let t = 0;
    let horizon = 0;
    const lastEnd = () => agents.reduce((m, a) => Math.max(m, a.busyUntil), 0);
    while (next < pending.length || waiting.length > 0 || t < lastEnd()) {
        // 1. completions: an agent whose call ends at t is free from t; idleSince records it
        for (const a of agents)
            if (a.busyUntil === t && a.handled > 0)
                a.idleSince = t;
        // 2. arrivals
        while (next < pending.length && pending[next].arrival === t)
            waiting.push(pending[next++]);
        // 3. abandons
        for (let i = waiting.length - 1; i >= 0; i--) {
            const c = waiting[i];
            if (c.arrival + c.patienceSeconds <= t) {
                const o = outcome.get(c.id);
                o.abandonedAt = t;
                o.waitSeconds = t - c.arrival;
                horizon = Math.max(horizon, t);
                waiting.splice(i, 1);
            }
        }
        // 4. routing
        let assigned = true;
        while (assigned && waiting.length) {
            assigned = false;
            const free = agents.filter((a) => a.busyUntil <= t).sort((x, y) => x.idleSince - y.idleSince || (x.agent.id < y.agent.id ? -1 : 1));
            for (const a of free) {
                const prof = profiles.get(a.agent.routingProfileId);
                let best = null;
                for (const c of waiting) {
                    const pq = prof.queues.find((q) => q.queueId === c.queueId);
                    if (!pq)
                        continue;
                    const wait = t - c.arrival;
                    if (wait < pq.delaySeconds)
                        continue;
                    if (c.routingCriteria && !agentMatches(a.agent, activeStep(c.routingCriteria.steps, wait)))
                        continue;
                    const key = [pq.priority, c.priority ?? DEFAULT_PRIORITY, c.arrival - (c.timeAdjustmentSeconds || 0), c.id];
                    if (!best || key[0] < best.key[0] || (key[0] === best.key[0] && (key[1] < best.key[1] || (key[1] === best.key[1] && (key[2] < best.key[2] || (key[2] === best.key[2] && key[3] < best.key[3])))))) {
                        best = { c, key };
                    }
                }
                if (best) {
                    const c = best.c;
                    waiting.splice(waiting.indexOf(c), 1);
                    const o = outcome.get(c.id);
                    o.answeredAt = t;
                    o.agentId = a.agent.id;
                    o.waitSeconds = t - c.arrival;
                    a.busyUntil = t + c.handleSeconds;
                    a.handled++;
                    a.busySeconds += c.handleSeconds;
                    horizon = Math.max(horizon, a.busyUntil);
                    assigned = true;
                    break; // re-sort availability after every assignment
                }
            }
        }
        // jump to the next interesting second when nothing can change before it
        const candidates = [];
        if (next < pending.length)
            candidates.push(pending[next].arrival);
        for (const a of agents)
            if (a.busyUntil > t)
                candidates.push(a.busyUntil);
        for (const c of waiting) {
            candidates.push(c.arrival + c.patienceSeconds);
            for (const p of config.routingProfiles)
                for (const q of p.queues)
                    if (q.queueId === c.queueId && c.arrival + q.delaySeconds > t)
                        candidates.push(c.arrival + q.delaySeconds);
            if (c.routingCriteria) {
                let acc = c.arrival;
                for (const s of c.routingCriteria.steps) {
                    if (s.expirySeconds === undefined)
                        break;
                    acc += s.expirySeconds;
                    if (acc > t)
                        candidates.push(acc);
                }
            }
        }
        const future = candidates.filter((x) => x > t);
        if (!future.length)
            break;
        t = Math.min(...future);
    }
    const outs = contacts.map((c) => outcome.get(c.id));
    const queues = {};
    for (const q of config.queues)
        queues[q.id] = summarize(outs.filter((o) => o.queueId === q.id), config.serviceLevelThresholdSeconds);
    const span = Math.max(horizon, 1);
    const agentStats = {};
    for (const a of agents)
        agentStats[a.agent.id] = { handled: a.handled, busySeconds: a.busySeconds, occupancy: a.busySeconds / span };
    return { horizon, queues, agents: agentStats, overall: summarize(outs, config.serviceLevelThresholdSeconds), contacts: outs };
}
