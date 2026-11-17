// Loaders for the w8-t1 tests.
import * as fs from "fs";
import * as path from "path";
import { Inventory } from "../pipeline/types";

export const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
const read = (p: string) => JSON.parse(fs.readFileSync(path.join(root, p), "utf8"));
export const prod = (): Inventory => read("inventory/prod.json");
export const dev = (): Inventory => read("export/dev/inventory.json");
export const releaseArtifacts = (): { file: string; kind: string; name: string; content: string }[] =>
  fs.readdirSync(path.join(root, "release/prod")).filter((f) => f.endsWith(".json")).sort()
    .map((f) => ({ file: f, ...read(path.join("release/prod", f)) }));
export const devContent = (kind: "flows" | "modules", file: string): string => {
  const j = read(path.join("export/dev", kind, file));
  return (j.ContactFlow || j.ContactFlowModule).Content;
};
