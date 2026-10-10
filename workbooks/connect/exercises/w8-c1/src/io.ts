// File loading and writing for the CLI. Provided; you should not need to change it.
import * as fs from "fs";
import * as path from "path";
import { DevExport, Inventory, PromotionResult } from "./types";

export function loadExport(dir: string): DevExport {
  const read = (p: string) => JSON.parse(fs.readFileSync(p, "utf8"));
  const list = (sub: string) =>
    fs.readdirSync(path.join(dir, sub)).filter((f) => f.endsWith(".json")).sort().map((f) => read(path.join(dir, sub, f)));
  return { inventory: read(path.join(dir, "inventory.json")), flows: list("flows"), modules: list("modules") };
}

export function loadInventory(file: string): Inventory {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

export function writeResult(outDir: string, result: PromotionResult): void {
  fs.rmSync(outDir, { recursive: true, force: true });
  fs.mkdirSync(outDir, { recursive: true });
  result.artifacts.forEach((a, i) => {
    const file = `${String(i + 1).padStart(2, "0")}-${a.kind}-${a.name.replace(/[^A-Za-z0-9]+/g, "-").toLowerCase()}.json`;
    fs.writeFileSync(path.join(outDir, file), JSON.stringify(a, null, 2) + "\n");
  });
  fs.writeFileSync(
    path.join(outDir, "report.json"),
    JSON.stringify({ ok: result.ok, replacements: result.replacements, problems: result.problems }, null, 2) + "\n",
  );
}
