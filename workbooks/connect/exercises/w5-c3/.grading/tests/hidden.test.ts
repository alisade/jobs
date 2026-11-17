// Hidden gates for connect/w5-c3: a holdout set the learner never saw, scored with a pristine copy
// of the simulator (so editing src/sim.ts does not help), plus anti-overfitting and config checks.
import * as fs from "fs";
import * as path from "path";
import { evaluate, loadConfig, parseJsonl, tokens } from "./sim-pristine";

const root = path.resolve(__dirname, "../..");
const yamlText = fs.readFileSync(path.join(root, "tuning/agent.yaml"), "utf8");
const cfg = loadConfig(yamlText);
const visible = parseJsonl(fs.readFileSync(path.join(root, "eval/eval-set.jsonl"), "utf8"));
const holdout = parseJsonl(fs.readFileSync(path.join(__dirname, "holdout.jsonl"), "utf8"));
const vis = evaluate(cfg, visible).metrics;
const hold = evaluate(cfg, holdout).metrics;

const BASELINE = `model: {temperature: 0.7, maxTokens: 400}
intents:
  - {name: ResetPassword, description: Password help}
  - {name: UnlockAccount, description: Account issues}
  - {name: ReportOutage, description: Problems}
  - {name: HowTo, description: Questions}
  - {name: RequestAccess, description: Access}
  - {name: CheckTicketStatus, description: Tickets}
  - {name: TalkToAgent, description: Agent}
classifier: {confidenceThreshold: 0.9}
retrieval: {topK: 1, minScore: 0.75}
answer: {requireCitations: false}
`;
const base = evaluate(loadConfig(BASELINE), visible).metrics;

describe("scored with the pristine simulator", () => {
  test("visible accuracy >= 0.85 and beats the baseline by >= 0.5", () => {
    expect(vis.intentAccuracy).toBeGreaterThanOrEqual(0.85);
    expect(vis.intentAccuracy - base.intentAccuracy).toBeGreaterThanOrEqual(0.5);
  });
  test("visible containment >= 0.45", () => expect(vis.containment).toBeGreaterThanOrEqual(0.45));
  test("visible p95 latency <= 1800 ms", () => expect(vis.p95LatencyMs).toBeLessThanOrEqual(1800));
});

describe("holdout (generalization)", () => {
  test("holdout accuracy >= 0.80", () => expect(hold.intentAccuracy).toBeGreaterThanOrEqual(0.8));
  test("holdout containment >= 0.35", () => expect(hold.containment).toBeGreaterThanOrEqual(0.35));
  test("holdout misroutes <= 5%", () => expect(hold.misrouteRate).toBeLessThanOrEqual(0.05));
  test("holdout hallucinations: none", () => expect(hold.hallucinationRate).toBe(0));
  test("accuracy gap visible vs holdout <= 0.10 (not overfit)", () => expect(vis.intentAccuracy - hold.intentAccuracy).toBeLessThanOrEqual(0.1));
});

describe("config hygiene", () => {
  test("temperature 0 and maxTokens <= 300 for deterministic, short voice answers", () => {
    expect(cfg.model.temperature).toBe(0);
    expect(cfg.model.maxTokens).toBeLessThanOrEqual(300);
  });
  test("citations required (grounding check on)", () => expect(cfg.answer.requireCitations).toBe(true));
  test("same seven intents, none added or removed", () => {
    expect(cfg.intents.map((i) => i.name).sort()).toEqual(["CheckTicketStatus", "HowTo", "ReportOutage", "RequestAccess", "ResetPassword", "TalkToAgent", "UnlockAccount"]);
  });
  test("no eval utterance pasted in as an example or description", () => {
    const norm = (s: string) => tokens(s).join(" ");
    const evalSet = new Set(visible.map((c) => norm(c.utterance)));
    const used = cfg.intents.flatMap((i) => [i.description, ...(i.examples || [])]).map(norm);
    expect(used.filter((u) => evalSet.has(u))).toEqual([]);
  });
  test("threshold is a real gate (0.3 - 0.8)", () => {
    expect(cfg.classifier.confidenceThreshold).toBeGreaterThanOrEqual(0.3);
    expect(cfg.classifier.confidenceThreshold).toBeLessThanOrEqual(0.8);
  });
});
