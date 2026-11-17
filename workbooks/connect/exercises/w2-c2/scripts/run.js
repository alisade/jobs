// Run the simulator on a config and the published stream: node scripts/run.js <config.json> [seed]
// Loads src/*.ts through the TypeScript compiler on the fly (no build step).
const fs = require("fs");
const path = require("path");
const ts = require("typescript");
require.extensions[".ts"] = (m, file) => {
  const out = ts.transpileModule(fs.readFileSync(file, "utf8"), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true } });
  m._compile(out.outputText, file);
};
const root = path.resolve(__dirname, "..");
const { simulate } = require(path.join(root, "src/sim.ts"));
const { generateContacts } = require(path.join(root, "src/generate.ts"));
const cfg = JSON.parse(fs.readFileSync(path.resolve(process.argv[2] || "inputs/lfg-config.json"), "utf8"));
const spec = JSON.parse(fs.readFileSync(path.join(root, "inputs/stream-spec.json"), "utf8"));
if (process.argv[3]) spec.seed = Number(process.argv[3]);
const contacts = generateContacts(spec);
const r = simulate(cfg, contacts);
const pct = (x) => (100 * x).toFixed(1).padStart(6) + "%";
console.log(`seed ${spec.seed}  contacts ${contacts.length}  SL threshold ${cfg.serviceLevelThresholdSeconds}s`);
console.log("queue              offered  handled  aband     SL      ASA   maxWait");
for (const [q, s] of Object.entries(r.queues).concat([["OVERALL", r.overall]])) {
  console.log(`${q.padEnd(18)} ${String(s.offered).padStart(7)} ${String(s.handled).padStart(8)} ${pct(s.abandonRate)} ${pct(s.serviceLevel)} ${s.asaSeconds.toFixed(1).padStart(7)}s ${String(s.maxWaitSeconds).padStart(7)}s`);
}
const occ = Object.values(r.agents).map((a) => a.occupancy);
console.log(`agents ${occ.length}  mean occupancy ${pct(occ.reduce((a, b) => a + b, 0) / Math.max(occ.length, 1))}`);
