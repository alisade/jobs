// make eval: score tuning/agent.yaml against eval/eval-set.jsonl with the lfg-sim-1 simulator.
import * as fs from "fs";
import * as path from "path";
import { evaluate, loadConfig, parseJsonl } from "../src/sim";

const root = path.resolve(__dirname, "..");
const cfgPath = process.argv[2] || path.join(root, "tuning/agent.yaml");
const cases = parseJsonl(fs.readFileSync(path.join(root, "eval/eval-set.jsonl"), "utf8"));
const { metrics, results } = evaluate(loadConfig(fs.readFileSync(cfgPath, "utf8")), cases);
const show = process.env.SHOW || "errors";
for (const r of results) {
  if (show === "all" || r.outcome === "misrouted" || r.outcome === "hallucinated" || (r.outcome === "handoff" && r.gold !== "Fallback")) {
    const u = cases.find((c) => c.id === r.id)!.utterance;
    console.log(`${r.id}  gold=${r.gold.padEnd(17)} pred=${r.predicted.padEnd(17)} conf=${r.confidence.toFixed(3)} ${r.outcome.padEnd(12)} "${u}"`);
  }
}
console.log(JSON.stringify(metrics, null, 2));
