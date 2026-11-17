// Erlang C staffing math for the LFG service desk.
//
// Units: seconds for times, Erlangs for traffic. All functions are pure.
// The previous WFM analyst's spreadsheet port is below; it "works for small teams".
// Finish the TODOs and fix what is wrong. Keep the exported signatures.

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

/** Offered load in Erlangs: arrival rate x average handle time. */
export function trafficIntensity(callsPerInterval: number, intervalSeconds: number, ahtSeconds: number): number {
  return (callsPerInterval * ahtSeconds) / intervalSeconds;
}

function factorial(n: number): number {
  let f = 1;
  for (let i = 2; i <= n; i++) f *= i;
  return f;
}

/** Erlang B blocking probability. */
export function erlangB(agents: number, erlangs: number): number {
  // TODO: implement (hint: there is a recursion that never overflows)
  throw new Error("not implemented");
}

/** Erlang C probability that a contact waits. */
export function erlangC(agents: number, erlangs: number): number {
  const top = (Math.pow(erlangs, agents) / factorial(agents)) * (agents / (agents - erlangs));
  let sum = 0;
  for (let k = 0; k < agents; k++) sum += Math.pow(erlangs, k) / factorial(k);
  return top / (sum + top);
}

/** Fraction of contacts answered within thresholdSeconds. */
export function serviceLevel(agents: number, erlangs: number, ahtSeconds: number, thresholdSeconds: number): number {
  const c = erlangC(agents, erlangs);
  return 1 - c * Math.exp((-(agents - erlangs) * thresholdSeconds) / ahtSeconds);
}

/** Average speed of answer in seconds. */
export function averageSpeedOfAnswer(agents: number, erlangs: number, ahtSeconds: number): number {
  // TODO
  throw new Error("not implemented");
}

/** Agent occupancy: share of logged-in time spent on contacts. */
export function occupancy(agents: number, erlangs: number): number {
  return erlangs / agents;
}

/** Smallest staffing that meets the service-level target (and the occupancy cap, if given). */
export function agentsRequired(input: StaffingInput): StaffingResult {
  const A = trafficIntensity(input.callsPerInterval, input.intervalSeconds, input.ahtSeconds);
  let n = Math.ceil(A);
  while (serviceLevel(n, A, input.ahtSeconds, input.thresholdSeconds) < input.targetServiceLevel) n++;
  const shrink = input.shrinkage ?? 0;
  // TODO: occupancy cap, concurrency, input validation
  return {
    erlangs: A,
    agents: n,
    scheduled: Math.round(n * (1 + shrink)),
    serviceLevel: serviceLevel(n, A, input.ahtSeconds, input.thresholdSeconds),
    asaSeconds: 0,
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
  // TODO
  throw new Error("not implemented");
}
