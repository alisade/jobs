// Erlang C staffing math for the LFG service desk (reference solution).
//
// Units: seconds for times, Erlangs for traffic. All functions are pure.

export type StaffingInput = {
  callsPerInterval: number;
  intervalSeconds: number;
  ahtSeconds: number;
  targetServiceLevel: number; // e.g. 0.8
  thresholdSeconds: number; // e.g. 20
  maxOccupancy?: number; // e.g. 0.85 (optional cap)
  shrinkage?: number; // e.g. 0.3 = 30% of paid time not on contacts
  concurrency?: number; // contacts one agent works at once (chat); default 1
  maxAgents?: number; // search ceiling, default 10000
};

export type StaffingResult = {
  erlangs: number;
  agents: number; // productive agents (seats) needed on contacts
  scheduled: number; // agents to schedule after shrinkage
  serviceLevel: number;
  asaSeconds: number;
  occupancy: number;
  probabilityOfWait: number;
};

function check(cond: boolean, msg: string): void {
  if (!cond) throw new RangeError(msg);
}

/** Offered load in Erlangs: arrival rate x average handle time. */
export function trafficIntensity(callsPerInterval: number, intervalSeconds: number, ahtSeconds: number): number {
  check(Number.isFinite(callsPerInterval) && callsPerInterval >= 0, "callsPerInterval must be >= 0");
  check(Number.isFinite(intervalSeconds) && intervalSeconds > 0, "intervalSeconds must be > 0");
  check(Number.isFinite(ahtSeconds) && ahtSeconds > 0, "ahtSeconds must be > 0");
  return (callsPerInterval * ahtSeconds) / intervalSeconds;
}

/** Erlang B blocking probability via the stable recursion B(k) = A B(k-1) / (k + A B(k-1)). */
export function erlangB(agents: number, erlangs: number): number {
  check(Number.isInteger(agents) && agents >= 0, "agents must be a non-negative integer");
  check(erlangs >= 0, "erlangs must be >= 0");
  let b = 1;
  for (let k = 1; k <= agents; k++) b = (erlangs * b) / (k + erlangs * b);
  return b;
}

/** Erlang C probability that a contact waits. 1 when the queue is unstable (agents <= load). */
export function erlangC(agents: number, erlangs: number): number {
  check(Number.isInteger(agents) && agents >= 0, "agents must be a non-negative integer");
  check(erlangs >= 0, "erlangs must be >= 0");
  if (erlangs === 0) return 0;
  if (agents <= erlangs) return 1;
  const b = erlangB(agents, erlangs);
  return (agents * b) / (agents - erlangs * (1 - b));
}

/** Fraction of contacts answered within thresholdSeconds. */
export function serviceLevel(agents: number, erlangs: number, ahtSeconds: number, thresholdSeconds: number): number {
  check(thresholdSeconds >= 0, "thresholdSeconds must be >= 0");
  check(ahtSeconds > 0, "ahtSeconds must be > 0");
  if (erlangs === 0) return 1;
  if (agents <= erlangs) return 0;
  const c = erlangC(agents, erlangs);
  return 1 - c * Math.exp((-(agents - erlangs) * thresholdSeconds) / ahtSeconds);
}

/** Average speed of answer in seconds (Infinity when unstable). */
export function averageSpeedOfAnswer(agents: number, erlangs: number, ahtSeconds: number): number {
  if (erlangs === 0) return 0;
  if (agents <= erlangs) return Infinity;
  return (erlangC(agents, erlangs) * ahtSeconds) / (agents - erlangs);
}

/** Agent occupancy: share of logged-in time spent on contacts (capped at 1). */
export function occupancy(agents: number, erlangs: number): number {
  check(agents > 0, "agents must be > 0");
  return Math.min(1, erlangs / agents);
}

/** Smallest staffing that meets the service-level target (and the occupancy cap, if given). */
export function agentsRequired(input: StaffingInput): StaffingResult {
  const sl = input.targetServiceLevel;
  check(sl > 0 && sl < 1, "targetServiceLevel must be in (0, 1)");
  const shrink = input.shrinkage ?? 0;
  check(shrink >= 0 && shrink < 1, "shrinkage must be in [0, 1)");
  const conc = input.concurrency ?? 1;
  check(Number.isInteger(conc) && conc >= 1, "concurrency must be a positive integer");
  if (input.maxOccupancy !== undefined) check(input.maxOccupancy > 0 && input.maxOccupancy <= 1, "maxOccupancy must be in (0, 1]");
  const A = trafficIntensity(input.callsPerInterval, input.intervalSeconds, input.ahtSeconds);
  const ceiling = input.maxAgents ?? 10000;

  if (A === 0) {
    return { erlangs: 0, agents: 0, scheduled: 0, serviceLevel: 1, asaSeconds: 0, occupancy: 0, probabilityOfWait: 0 };
  }
  // Servers are concurrent contact slots; with concurrency c one agent provides c slots.
  let n = Math.max(1, Math.floor(A) + 1);
  if (input.maxOccupancy !== undefined) n = Math.max(n, Math.ceil(A / input.maxOccupancy - 1e-9));
  for (; n <= ceiling * conc; n++) {
    if (serviceLevel(n, A, input.ahtSeconds, input.thresholdSeconds) >= sl) break;
  }
  check(n <= ceiling * conc, `no staffing up to maxAgents ${ceiling} meets the target`);
  const agents = Math.ceil(n / conc);
  return {
    erlangs: A,
    agents,
    scheduled: Math.ceil(agents / (1 - shrink) - 1e-9),
    serviceLevel: serviceLevel(n, A, input.ahtSeconds, input.thresholdSeconds),
    asaSeconds: averageSpeedOfAnswer(n, A, input.ahtSeconds),
    occupancy: occupancy(n, A),
    probabilityOfWait: erlangC(n, A),
  };
}

export type Forecast = {
  intervalSeconds: number;
  ahtSeconds: number;
  serviceLevel: { target: number; thresholdSeconds: number };
  maxOccupancy?: number;
  shrinkage?: number;
  intervals: { start: string; calls: number }[];
};

export type PlanRow = { start: string; calls: number } & StaffingResult;

/** Interval-by-interval staffing plan plus the peak and total scheduled agent-hours. */
export function staffingPlan(f: Forecast): { rows: PlanRow[]; peakScheduled: number; scheduledAgentHours: number } {
  const rows = f.intervals.map((iv) => ({
    start: iv.start,
    calls: iv.calls,
    ...agentsRequired({
      callsPerInterval: iv.calls,
      intervalSeconds: f.intervalSeconds,
      ahtSeconds: f.ahtSeconds,
      targetServiceLevel: f.serviceLevel.target,
      thresholdSeconds: f.serviceLevel.thresholdSeconds,
      maxOccupancy: f.maxOccupancy,
      shrinkage: f.shrinkage,
    }),
  }));
  const peakScheduled = rows.reduce((m, r) => Math.max(m, r.scheduled), 0);
  const scheduledAgentHours = rows.reduce((s, r) => s + (r.scheduled * f.intervalSeconds) / 3600, 0);
  return { rows, peakScheduled, scheduledAgentHours };
}
