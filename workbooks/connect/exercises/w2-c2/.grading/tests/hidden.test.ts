// Hidden tests for connect/w2-c2.
import * as fs from "fs";
import * as path from "path";
import { simulate, activeStep, agentMatches } from "../../src/sim";
import { generateContacts } from "../../src/generate";
import { config, contact, outcome } from "../helpers";

const root = path.resolve(__dirname, "../..");
const read = (p: string) => JSON.parse(fs.readFileSync(path.join(root, p), "utf8"));
const rp1 = (queues: { queueId: string; priority: number; delaySeconds: number }[]) => [{ id: "rp", queues }];
const sap4 = { steps: [{ expirySeconds: 30, conditions: [{ attribute: "Application", value: "SAP", minLevel: 4 }] }, { expirySeconds: 90, conditions: [{ attribute: "Application", value: "SAP", minLevel: 2 }] }] };

describe("routing criteria", () => {
  test("activeStep walks the steps by cumulative expiry; null after the last expiring step", () => {
    expect(activeStep(sap4.steps, 0)).toBe(sap4.steps[0]);
    expect(activeStep(sap4.steps, 29)).toBe(sap4.steps[0]);
    expect(activeStep(sap4.steps, 30)).toBe(sap4.steps[1]);
    expect(activeStep(sap4.steps, 119)).toBe(sap4.steps[1]);
    expect(activeStep(sap4.steps, 120)).toBeNull();
  });
  test("a step without expiry never expires", () => {
    const steps = [{ conditions: [{ attribute: "Language", value: "es", minLevel: 3 }] }];
    expect(activeStep(steps, 100000)).toBe(steps[0]);
  });
  test("agentMatches requires every condition at or above the level", () => {
    const step = { conditions: [{ attribute: "Application", value: "SAP", minLevel: 3 }, { attribute: "Language", value: "es", minLevel: 2 }] };
    expect(agentMatches({ id: "a", routingProfileId: "rp", proficiencies: [{ attribute: "Application", value: "SAP", level: 3 }, { attribute: "Language", value: "es", level: 2 }] }, step)).toBe(true);
    expect(agentMatches({ id: "a", routingProfileId: "rp", proficiencies: [{ attribute: "Application", value: "SAP", level: 5 }] }, step)).toBe(false);
    expect(agentMatches({ id: "a", routingProfileId: "rp" }, null)).toBe(true);
  });
  test("a contact waits for step 1 to expire when only a lower-proficiency agent is free", () => {
    const cfg = config(rp1([{ queueId: "q1", priority: 1, delaySeconds: 0 }]), [{ id: "a1", routingProfileId: "rp", proficiencies: [{ attribute: "Application", value: "SAP", level: 2 }] }]);
    const r = simulate(cfg, [contact("c1", "q1", 0, 100, 10000, { routingCriteria: sap4 })]);
    expect(outcome(r, "c1").answeredAt).toBe(30);
  });
  test("after every step expires any agent on the queue can take it", () => {
    const cfg = config(rp1([{ queueId: "q1", priority: 1, delaySeconds: 0 }]), [{ id: "a1", routingProfileId: "rp" }]);
    const r = simulate(cfg, [contact("c1", "q1", 0, 100, 10000, { routingCriteria: sap4 })]);
    expect(outcome(r, "c1").answeredAt).toBe(120);
  });
  test("a matching agent answers immediately", () => {
    const cfg = config(rp1([{ queueId: "q1", priority: 1, delaySeconds: 0 }]), [{ id: "a1", routingProfileId: "rp", proficiencies: [{ attribute: "Application", value: "SAP", level: 5 }] }]);
    expect(outcome(simulate(cfg, [contact("c1", "q1", 7, 100, 10000, { routingCriteria: sap4 })]), "c1").answeredAt).toBe(7);
  });
});

describe("agent and contact ordering", () => {
  test("the longest-idle agent gets the next contact", () => {
    const cfg = config(rp1([{ queueId: "q1", priority: 1, delaySeconds: 0 }]), [{ id: "a1", routingProfileId: "rp" }, { id: "a2", routingProfileId: "rp" }]);
    const r = simulate(cfg, [contact("x1", "q1", 0, 50), contact("x2", "q1", 0, 20), contact("next", "q1", 60, 10)]);
    expect(outcome(r, "x1").agentId).toBe("a1");
    expect(outcome(r, "next").agentId).toBe("a2");
  });
  test("contact priority orders contacts within a queue", () => {
    const cfg = config(rp1([{ queueId: "q1", priority: 1, delaySeconds: 0 }]), [{ id: "a1", routingProfileId: "rp" }]);
    const r = simulate(cfg, [contact("busy", "q1", 0), contact("old", "q1", 10), contact("exec", "q1", 20, 100, 10000, { priority: 1 })]);
    expect(outcome(r, "exec").answeredAt).toBe(100);
    expect(outcome(r, "old").answeredAt).toBe(200);
  });
  test("queue time adjustment makes a contact count as older", () => {
    const cfg = config(rp1([{ queueId: "q1", priority: 1, delaySeconds: 0 }]), [{ id: "a1", routingProfileId: "rp" }]);
    const r = simulate(cfg, [contact("busy", "q1", 0), contact("old", "q1", 10), contact("bumped", "q1", 30, 100, 10000, { timeAdjustmentSeconds: 60 })]);
    expect(outcome(r, "bumped").answeredAt).toBe(100);
  });
  test("routing profile priority beats contact priority across queues", () => {
    const cfg = config(rp1([{ queueId: "q1", priority: 1, delaySeconds: 0 }, { queueId: "q2", priority: 2, delaySeconds: 0 }]), [{ id: "a1", routingProfileId: "rp" }]);
    const r = simulate(cfg, [contact("busy", "q1", 0), contact("vip-q2", "q2", 5, 100, 10000, { priority: 1 }), contact("plain-q1", "q1", 50)]);
    expect(outcome(r, "plain-q1").answeredAt).toBe(100);
  });
  test("a delayed queue still serves its own priority-1 agents immediately", () => {
    const cfg = config(
      [{ id: "own", queues: [{ queueId: "q2", priority: 1, delaySeconds: 0 }] }, { id: "overflow", queues: [{ queueId: "q2", priority: 1, delaySeconds: 45 }] }],
      [{ id: "a1", routingProfileId: "overflow" }, { id: "a2", routingProfileId: "own" }],
    );
    const r = simulate(cfg, [contact("c1", "q2", 0)]);
    expect(outcome(r, "c1").agentId).toBe("a2");
  });
  test("an agent on another queue's delay does not starve: it waits until the delay passes", () => {
    const cfg = config([{ id: "overflow", queues: [{ queueId: "q2", priority: 1, delaySeconds: 45 }] }], [{ id: "a1", routingProfileId: "overflow" }]);
    expect(outcome(simulate(cfg, [contact("c1", "q2", 3)]), "c1").answeredAt).toBe(48);
  });
  test("abandon is evaluated before routing in the same second", () => {
    const cfg = config(rp1([{ queueId: "q1", priority: 1, delaySeconds: 0 }]), [{ id: "a1", routingProfileId: "rp" }]);
    const r = simulate(cfg, [contact("busy", "q1", 0), contact("edge", "q1", 0, 100, 100)]);
    expect(outcome(r, "edge").abandonedAt).toBe(100);
    expect(outcome(r, "edge").agentId).toBeNull();
  });
});

describe("metrics", () => {
  test("service level counts abandons in the denominator and the threshold is inclusive", () => {
    const cfg = config(rp1([{ queueId: "q1", priority: 1, delaySeconds: 0 }]), [{ id: "a1", routingProfileId: "rp" }], ["q1"], 20);
    const r = simulate(cfg, [contact("a", "q1", 0, 20), contact("b", "q1", 0, 30), contact("c", "q1", 0, 10, 15)]);
    // a answered at 0, b answered at 20 (wait 20 <= 20), c abandons at 15
    expect(r.queues.q1.offered).toBe(3);
    expect(r.queues.q1.answeredWithinThreshold).toBe(2);
    expect(r.queues.q1.serviceLevel).toBeCloseTo(2 / 3, 10);
    expect(r.queues.q1.asaSeconds).toBeCloseTo(10, 10);
    expect(r.queues.q1.abandonRate).toBeCloseTo(1 / 3, 10);
  });
  test("an empty queue reports SL 1 and zeros", () => {
    const cfg = config(rp1([{ queueId: "q1", priority: 1, delaySeconds: 0 }]), [{ id: "a1", routingProfileId: "rp" }]);
    const r = simulate(cfg, [contact("a", "q1", 0, 10)]);
    expect(r.queues.q2).toEqual(expect.objectContaining({ offered: 0, serviceLevel: 1, asaSeconds: 0, abandonRate: 0 }));
  });
  test("occupancy is busy time over the horizon (last finish or abandon)", () => {
    const cfg = config(rp1([{ queueId: "q1", priority: 1, delaySeconds: 0 }]), [{ id: "a1", routingProfileId: "rp" }, { id: "a2", routingProfileId: "rp" }]);
    const r = simulate(cfg, [contact("a", "q1", 0, 100), contact("b", "q1", 0, 50)]);
    expect(r.horizon).toBe(100);
    expect(r.agents.a1.occupancy).toBeCloseTo(1, 10);
    expect(r.agents.a2.occupancy).toBeCloseTo(0.5, 10);
  });
});

describe("robustness", () => {
  test("bad configs fail loudly", () => {
    expect(() => simulate(config([{ id: "rp", queues: [{ queueId: "nope", priority: 1, delaySeconds: 0 }] }], []), [])).toThrow();
    expect(() => simulate(config(rp1([{ queueId: "q1", priority: 1, delaySeconds: 0 }]), [{ id: "a", routingProfileId: "ghost" }]), [])).toThrow();
    expect(() => simulate(config(rp1([{ queueId: "q1", priority: 1, delaySeconds: 0 }]), []), [contact("d", "q1", 0), contact("d", "q1", 1)])).toThrow();
  });
  test("deterministic and does not mutate its inputs", () => {
    const cfg = read("inputs/lfg-config.json");
    const cs = generateContacts(read("inputs/stream-spec.json"));
    const before = JSON.stringify([cfg, cs]);
    const a = simulate(cfg, cs);
    const b = simulate(cfg, cs);
    expect(JSON.stringify(a)).toEqual(JSON.stringify(b));
    expect(JSON.stringify([cfg, cs])).toEqual(before);
  });
  test("20,000 contacts simulate in under 5 seconds", () => {
    const cfg = read("inputs/lfg-config.json");
    const spec = read("inputs/stream-spec.json");
    spec.durationSeconds = 7200 * 34;
    const cs = generateContacts(spec);
    expect(cs.length).toBeGreaterThan(19000);
    const t0 = Date.now();
    simulate(cfg, cs);
    expect(Date.now() - t0).toBeLessThan(5000);
  });
});

describe("LFG design", () => {
  test("baseline figures match the reference semantics exactly", () => {
    const r = simulate(read("inputs/lfg-config.json"), generateContacts(read("inputs/stream-spec.json")));
    const got = Object.fromEntries(Object.entries(r.queues).map(([q, s]) => [q, [s.offered, s.handled, s.abandoned, s.answeredWithinThreshold]]));
    expect(got).toEqual({ "q-password-reset": [291, 291, 0, 291], "q-general": [195, 188, 7, 173], "q-apps": [75, 60, 15, 40], "q-vip": [24, 13, 11, 11] });
  });
  test("tuned design keeps the same agents, proficiencies and queues", () => {
    const base = read("inputs/lfg-config.json");
    const tuned = read("inputs/tuned-config.json");
    const strip = (agents: any[]) => agents.map((a) => [a.id, JSON.stringify(a.proficiencies || [])]).sort();
    expect(strip(tuned.agents)).toEqual(strip(base.agents));
    expect(tuned.queues).toEqual(base.queues);
    expect(tuned.serviceLevelThresholdSeconds).toBe(base.serviceLevelThresholdSeconds);
  });
  test("tuned design: every queue >= 80%, VIP >= 90%, overall abandon rate <= 6%", () => {
    const r = simulate(read("inputs/tuned-config.json"), generateContacts(read("inputs/stream-spec.json")));
    for (const s of Object.values(r.queues)) expect(s.serviceLevel).toBeGreaterThanOrEqual(0.8);
    expect(r.queues["q-vip"].serviceLevel).toBeGreaterThanOrEqual(0.9);
    expect(r.overall.abandonRate).toBeLessThanOrEqual(0.06);
  });
});
