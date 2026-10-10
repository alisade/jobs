// Visible tests for connect/w2-c1. The grader adds more (edge cases, large centers, validation).
import { trafficIntensity, erlangC, serviceLevel, agentsRequired } from "../src/erlang";

// Textbook example: 100 calls per 30 minutes, AHT 180 s -> 10 Erlangs; target 80% in 20 s.
test("traffic intensity of the textbook example is 10 Erlangs", () => {
  expect(trafficIntensity(100, 1800, 180)).toBeCloseTo(10, 10);
});

test("probability of waiting with 13 agents on 10 Erlangs", () => {
  expect(erlangC(13, 10)).toBeCloseTo(0.28527, 4);
});

test("service level with 14 agents is about 88.8%", () => {
  expect(serviceLevel(14, 10, 180, 20)).toBeCloseTo(0.88835, 4);
});

test("80/20 needs 14 agents (13 gives 79.6%)", () => {
  const r = agentsRequired({ callsPerInterval: 100, intervalSeconds: 1800, ahtSeconds: 180, targetServiceLevel: 0.8, thresholdSeconds: 20 });
  expect(r.agents).toBe(14);
});
