// make promote ENV=prod  ->  dist/prod/NN-<kind>-<name>.json + dist/prod/report.json ; exit 1 on problems.
import * as path from "path";
import { loadExport, loadInventory, writeResult } from "./io";
import { promote } from "./promote";

const env = process.env.ENV || process.argv[2] || "test";
const root = path.resolve(__dirname, "..");
const result = promote(loadExport(path.join(root, "export/dev")), loadInventory(path.join(root, "envs", `${env}.json`)));
writeResult(path.join(root, "dist", env), result);
console.log(`${env}: ${result.artifacts.length} artifacts, ${result.replacements.length} replacements, ${result.problems.length} problems`);
for (const p of result.problems) console.log(`  ${p.reason.padEnd(18)} ${p.artifact} ${p.path} ${p.value} -- ${p.detail}`);
process.exit(result.ok ? 0 : 1);
