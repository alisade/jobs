// Hidden tests for connect/w2-c1. Expected values computed independently (Python, Erlang B recursion).
import * as fs from "fs";
import * as path from "path";
import {
  trafficIntensity, erlangB, erlangC, serviceLevel, averageSpeedOfAnswer, occupancy, agentsRequired, staffingPlan,
} from "../../src/erlang";

const base = { callsPerInterval: 100, intervalSeconds: 1800, ahtSeconds: 180, targetServiceLevel: 0.8, thresholdSeconds: 20 };

describe("core math", () => {
  test("Erlang B recursion", () => {
    expect(erlangB(0, 10)).toBe(1);
    expect(erlangB(13, 10)).toBeCloseTo(0.084339, 5);
  });
  test("Erlang C table for 10 Erlangs", () => {
    const want: Record<number, number> = { 11: 0.682118, 12: 0.449388, 13: 0.28527, 14: 0.174132, 15: 0.102042 };
    for (const [n, c] of Object.entries(want)) expect(erlangC(Number(n), 10)).toBeCloseTo(c, 5);
  });
  test("unstable queue: probability of wait is 1 and service level 0 when agents <= load", () => {
    expect(erlangC(10, 10)).toBe(1);
    expect(erlangC(8, 10)).toBe(1);
    expect(serviceLevel(10, 10, 180, 20)).toBe(0);
  });
  test("ASA with 14 agents is about 7.84 s and infinite when unstable", () => {
    expect(averageSpeedOfAnswer(14, 10, 180)).toBeCloseTo(7.8359, 3);
    expect(averageSpeedOfAnswer(10, 10, 180)).toBe(Infinity);
  });
  test("occupancy", () => {
    expect(occupancy(14, 10)).toBeCloseTo(0.714286, 5);
  });
  test("no traffic: no wait, full service level", () => {
    expect(erlangC(3, 0)).toBe(0);
    expect(serviceLevel(3, 0, 180, 20)).toBe(1);
  });
  test("large center (500 Erlangs) is numerically stable", () => {
    const c = erlangC(510, 500);
    expect(Number.isFinite(c)).toBe(true);
    expect(c).toBeCloseTo(0.55021, 4);
    expect(serviceLevel(515, 500, 180, 20)).toBeCloseTo(0.92560, 4);
  });
});

describe("agentsRequired", () => {
  test("returns the textbook figures", () => {
    const r = agentsRequired(base);
    expect(r.erlangs).toBeCloseTo(10, 10);
    expect(r.agents).toBe(14);
    expect(r.serviceLevel).toBeCloseTo(0.88835, 4);
    expect(r.asaSeconds).toBeCloseTo(7.8359, 3);
    expect(r.occupancy).toBeCloseTo(0.714286, 5);
    expect(r.probabilityOfWait).toBeCloseTo(0.174132, 5);
  });
  test("shrinkage: 14 productive agents at 30% shrinkage need 20 scheduled", () => {
    expect(agentsRequired({ ...base, shrinkage: 0.3 }).scheduled).toBe(20);
  });
  test("occupancy cap of 70% forces 15 agents", () => {
    const r = agentsRequired({ ...base, maxOccupancy: 0.7 });
    expect(r.agents).toBe(15);
    expect(r.occupancy).toBeLessThanOrEqual(0.7);
  });
  test("large center: 5000 calls / 30 min at 180 s needs 510 agents", () => {
    expect(agentsRequired({ ...base, callsPerInterval: 5000 }).agents).toBe(510);
  });
  test("chat with concurrency 3: 120 chats / 30 min, 600 s handle, 80% in 60 s -> 16 agents", () => {
    const r = agentsRequired({ callsPerInterval: 120, intervalSeconds: 1800, ahtSeconds: 600, targetServiceLevel: 0.8, thresholdSeconds: 60, concurrency: 3 });
    expect(r.agents).toBe(16);
  });
  test("tiny load still needs one agent; zero load needs none", () => {
    expect(agentsRequired({ ...base, callsPerInterval: 1 }).agents).toBe(1);
    const z = agentsRequired({ ...base, callsPerInterval: 0 });
    expect(z.agents).toBe(0);
    expect(z.scheduled).toBe(0);
  });
  test("invalid inputs are rejected with RangeError", () => {
    expect(() => agentsRequired({ ...base, shrinkage: 1 })).toThrow(RangeError);
    expect(() => agentsRequired({ ...base, targetServiceLevel: 1.2 })).toThrow(RangeError);
    expect(() => agentsRequired({ ...base, ahtSeconds: 0 })).toThrow(RangeError);
    expect(() => agentsRequired({ ...base, callsPerInterval: -5 })).toThrow(RangeError);
  });
  test("an impossible ceiling fails loudly instead of looping", () => {
    expect(() => agentsRequired({ ...base, maxAgents: 5 })).toThrow(RangeError);
  });
});

describe("staffingPlan for the LFG Monday forecast", () => {
  const f = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../../inputs/forecast-monday.json"), "utf8"));
  test("per-interval scheduled agents", () => {
    const p = staffingPlan(f);
    expect(p.rows.map((r) => r.scheduled)).toEqual([9, 14, 21, 30, 34, 37, 37, 33, 31, 30, 28, 28, 30, 28, 27, 25, 24, 23, 20, 18, 15, 12, 9, 8, 6, 6, 5, 3]);
  });
  test("peak and scheduled agent-hours", () => {
    const p = staffingPlan(f);
    expect(p.peakScheduled).toBe(37);
    expect(p.scheduledAgentHours).toBeCloseTo(295.5, 6);
  });
  test("traffic intensity helper agrees with the plan", () => {
    expect(trafficIntensity(99, 1800, 372)).toBeCloseTo(20.46, 6);
  });
});
