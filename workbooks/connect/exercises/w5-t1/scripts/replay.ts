// Replay the recorded portal-chat traffic through THIS checkout's exporter + retriever against the
// local knowledge base stand-in. Prints a per-caller report; with --out <dir> also writes the
// retrieval log and the exported sidecars (used by make setup to build the incident bundle).
import * as fs from "fs";
import * as path from "path";
import { exportAll } from "../src/exporter";
import { retrieve } from "../src/retriever";
import { loadArticles, makeKb } from "../src/kbsim";

export async function replay() {
  const root = path.resolve(__dirname, "..");
  const traffic = JSON.parse(fs.readFileSync(path.join(root, "data/replay-traffic.json"), "utf8"));
  const objects = exportAll(loadArticles());
  const kb = makeKb(objects);
  const rows: any[] = [];
  for (const t of traffic.traffic) {
    const who = traffic.callers[t.caller];
    const r = await retrieve(kb.retrieveFn, t.query, who);
    const returned = r.results.map((x) => ({ articleId: x.metadata.articleId, score: x.score, audience: x.metadata.audience, department: x.metadata.department ?? x.metadata.dept, status: x.metadata.status }));
    const leaks = returned.filter((x) => (x.audience === "restricted" && x.department !== who.department) || x.status !== "published"
      || (who.employeeType === "contractor" && x.audience === "all-employees") || (!who.callerVerified && x.audience !== "public-help"));
    rows.push({ contactId: t.contactId, caller: t.caller, department: who.department || "-", query: t.query, status: r.status, ...r.log, returned, leaked: leaks.map((x) => x.articleId) });
  }
  return { rows, objects };
}

if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  (async () => {
    const out = process.argv.indexOf("--out") > 0 ? process.argv[process.argv.indexOf("--out") + 1] : null;
    const { rows, objects } = await replay();
    for (const r of rows) {
      console.log(`${r.caller.padEnd(9)} ${r.query.padEnd(36)} filtered=${String(r.filteredCount).padEnd(2)} fallback=${String(r.fallback).padEnd(10)} -> ${r.returned.map((x: any) => x.articleId).join(",") || "(none)"}${r.leaked.length ? "  LEAK " + r.leaked.join(",") : ""}`);
    }
    const leaks = rows.filter((r) => r.leaked.length).length;
    console.log(`\n${rows.length} contacts replayed, ${leaks} returned articles the caller must not see, ${rows.filter((r) => r.fallback).length} used the unfiltered fallback`);
    if (out) {
      fs.mkdirSync(path.join(out, "sidecars"), { recursive: true });
      fs.writeFileSync(path.join(out, "retrieval-log.jsonl"), rows.map((r, i) => JSON.stringify({ ts: `2026-10-07T${String(13 + Math.floor(i / 6)).padStart(2, "0")}:${String((i * 7) % 60).padStart(2, "0")}:11Z`, level: "INFO", logger: "helpdesk-rag.retriever", ...r })).join("\n") + "\n");
      for (const o of objects) fs.writeFileSync(path.join(out, "sidecars", path.basename(o.key) + ".metadata.json"), JSON.stringify(o.sidecar, null, 2) + "\n");
    }
  })();
}
