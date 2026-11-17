#!/usr/bin/env node
// make report FROM=2026-09-20 TO=2026-10-07 : run THIS checkout's report code over the incident S3 mirror
// and print the CSV (what Finance would receive). Transpiles src/*.ts on the fly with the shared typescript.
"use strict";
const fs = require("fs");
const os = require("os");
const path = require("path");
const ts = require("typescript");
const root = path.resolve(__dirname, "..");
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "w6t1-"));
for (const f of fs.readdirSync(path.join(root, "src")).filter((f) => f.endsWith(".ts"))) {
  const out = ts.transpileModule(fs.readFileSync(path.join(root, "src", f), "utf8"), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true } });
  fs.writeFileSync(path.join(tmp, f.replace(/\.ts$/, ".js")), out.outputText);
}
const { LocalS3 } = require(path.join(tmp, "s3mirror.js"));
const report = require(path.join(tmp, "report.js"));
const cfg = JSON.parse(fs.readFileSync(path.join(root, "config/report-config.json"), "utf8"));
const rows = report.buildReport(new LocalS3(path.join(root, "incident/s3")), cfg, process.env.FROM || "2026-09-20", process.env.TO || "2026-10-07");
process.stdout.write(report.toCsv(rows));
console.error(`${rows.length} rows`);
fs.rmSync(tmp, { recursive: true, force: true });
