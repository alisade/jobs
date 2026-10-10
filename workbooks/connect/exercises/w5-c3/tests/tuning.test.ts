// Visible go-live gates for connect/w5-c3 (eval/eval-set.jsonl). The grader adds a hidden holdout set.
import * as fs from "fs";
import * as path from "path";
import { evaluate, loadConfig, parseJsonl } from "../src/sim";

const root = path.resolve(__dirname, "..");
const cfg = loadConfig(fs.readFileSync(path.join(root, "tuning/agent.yaml"), "utf8"));
const { metrics } = evaluate(cfg, parseJsonl(fs.readFileSync(path.join(root, "eval/eval-set.jsonl"), "utf8")));

test("intent accuracy >= 0.85", () => expect(metrics.intentAccuracy).toBeGreaterThanOrEqual(0.85));
test("containment >= 0.45", () => expect(metrics.containment).toBeGreaterThanOrEqual(0.45));
test("no hallucinated answers", () => expect(metrics.hallucinationRate).toBe(0));
test("misroutes <= 5%", () => expect(metrics.misrouteRate).toBeLessThanOrEqual(0.05));
test("p95 latency <= 1800 ms", () => expect(metrics.p95LatencyMs).toBeLessThanOrEqual(1800));
