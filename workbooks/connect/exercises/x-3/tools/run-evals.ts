// make evals [BOT=bot/HelpDeskBot] [CASES=evals/utterances.csv]: replay utterances through the offline NLU.
import * as fs from "fs";
import { loadBot, recognize } from "./nlu";

const bot = loadBot(process.env.BOT || "bot/HelpDeskBot");
const rows = fs.readFileSync(process.env.CASES || "evals/utterances.csv", "utf8").trim().split("\n").slice(1).map((l) => l.split(","));
let ok = 0;
for (const [u, intent, sys] of rows) {
  const r = recognize(bot, u);
  const got = r.slots.System ? r.slots.System.interpretedValue : "";
  const pass = r.intent === intent && (!sys || got === sys);
  if (pass) ok++;
  console.log(`${pass ? "ok  " : "MISS"} ${u.padEnd(42)} -> ${r.intent.padEnd(18)} ${r.confidence === null ? "  -  " : r.confidence.toFixed(2)} System=${got || "-"}   (alts ${r.alternatives.map((a) => `${a.intent}:${a.confidence}`).join(" ")})`);
}
console.log(`\n${ok}/${rows.length} as expected (threshold ${bot.threshold})`);
