// Visible tests for connect/w2-c2. The grader adds more (criteria steps, idle order, contact
// priority, validation, exact baseline figures, performance).
import * as fs from "fs";
import * as path from "path";
import { simulate } from "../src/sim";
import { generateContacts } from "../src/generate";
import { config, contact, outcome } from "./helpers";

const one = (queues: { queueId: string; priority: number; delaySeconds: number }[]) =>
  config([{ id: "rp", queues }], [{ id: "a1", routingProfileId: "rp" }]);

test("single agent, FIFO: the second caller waits for the first to finish", () => {
  const r = simulate(one([{ queueId: "q1", priority: 1, delaySeconds: 0 }]), [contact("c1", "q1", 0), contact("c2", "q1", 10)]);
  expect(outcome(r, "c2").answeredAt).toBe(100);
  expect(outcome(r, "c2").waitSeconds).toBe(90);
});

test("a caller whose patience runs out abandons and is never answered", () => {
  const r = simulate(one([{ queueId: "q1", priority: 1, delaySeconds: 0 }]), [contact("c1", "q1", 0), contact("c2", "q1", 10, 100, 50)]);
  expect(outcome(r, "c2").abandonedAt).toBe(60);
  expect(outcome(r, "c2").answeredAt).toBeNull();
  expect(r.queues.q1.abandoned).toBe(1);
});

test("routing profile priority: a free agent takes the priority-1 queue even when priority-2 is older", () => {
  const cfg = one([{ queueId: "q1", priority: 1, delaySeconds: 0 }, { queueId: "q2", priority: 2, delaySeconds: 0 }]);
  const r = simulate(cfg, [contact("busy", "q1", 0), contact("old-q2", "q2", 5), contact("new-q1", "q1", 50)]);
  expect(outcome(r, "new-q1").answeredAt).toBe(100);
  expect(outcome(r, "old-q2").answeredAt).toBe(200);
});

test("routing profile delay: an idle agent only takes the queue after the delay", () => {
  const r = simulate(one([{ queueId: "q2", priority: 1, delaySeconds: 30 }]), [contact("c1", "q2", 0)]);
  expect(outcome(r, "c1").answeredAt).toBe(30);
});

test("your tuned design meets the targets on the published stream", () => {
  const root = path.resolve(__dirname, "..");
  const spec = JSON.parse(fs.readFileSync(path.join(root, "inputs/stream-spec.json"), "utf8"));
  const tuned = JSON.parse(fs.readFileSync(path.join(root, "inputs/tuned-config.json"), "utf8"));
  const r = simulate(tuned, generateContacts(spec));
  for (const [q, s] of Object.entries(r.queues)) expect([q, s.serviceLevel >= 0.8]).toEqual([q, true]);
  expect(r.queues["q-vip"].serviceLevel).toBeGreaterThanOrEqual(0.9);
});
