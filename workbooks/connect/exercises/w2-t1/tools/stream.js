// Deterministic contact stream generator (environment).
Object.defineProperty(exports, "__esModule", { value: true });
exports.rng = rng;
exports.generateContacts = generateContacts;
/** mulberry32: tiny, fast, good enough for simulation; returns floats in [0, 1). */
function rng(seed) {
    let a = seed >>> 0;
    return () => {
        a = (a + 0x6d2b79f5) >>> 0;
        let t = a;
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}
const exp = (r, mean) => -Math.log(1 - r()) * mean;
function generateContacts(spec) {
    const r = rng(spec.seed);
    const out = [];
    for (const q of spec.queues) {
        let t = 0;
        let n = 0;
        while (true) {
            t += exp(r, 3600 / q.perHour);
            if (t >= spec.durationSeconds)
                break;
            out.push({
                id: `${q.queueId}-${String(++n).padStart(5, "0")}`,
                queueId: q.queueId,
                arrival: Math.floor(t),
                handleSeconds: Math.max(1, Math.round(exp(r, q.ahtSeconds))),
                patienceSeconds: Math.max(5, Math.round(exp(r, q.patienceSeconds))),
                ...(q.priority !== undefined ? { priority: q.priority } : {}),
                ...(q.routingCriteria ? { routingCriteria: q.routingCriteria } : {}),
            });
        }
    }
    return out.sort((a, b) => a.arrival - b.arrival || (a.id < b.id ? -1 : 1));
}
