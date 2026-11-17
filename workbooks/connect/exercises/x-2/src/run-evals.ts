// make evals [CONFIG=guardrail/helpdesk-guardrail.json] [CASES=evals/cases.jsonl]
// Replays the eval cases through the local guardrail stand-in and prints a confusion table.
import * as fs from "fs";
import { evaluate } from "./evaluator";

const config = JSON.parse(fs.readFileSync(process.env.CONFIG || "guardrail/helpdesk-guardrail.json", "utf8"));
const cases = fs.readFileSync(process.env.CASES || "evals/cases.jsonl", "utf8").trim().split("\n").map((l) => JSON.parse(l));
let ok = 0;
for (const c of cases) {
  const a = evaluate(config, c.input);
  const got = a.blocked ? "BLOCK" : "ALLOW";
  const why = [...a.topics.map((t) => `topic "${t.name}" via "${t.matchedExample}"`), ...a.contentFilters.map((f) => f.type), ...a.words.map((w) => `word ${w.match}`),
    ...a.pii.filter((p) => p.action !== "NONE").map((p) => `${p.type}:${p.action}`)].join("; ");
  if (got === c.expect) ok++;
  console.log(`${got === c.expect ? "ok  " : "MISS"} expect=${c.expect.padEnd(5)} got=${got.padEnd(5)} ${JSON.stringify(c.input)}${why ? "  <- " + why : ""}`);
}
console.log(`\n${ok}/${cases.length} as expected`);
