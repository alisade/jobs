// Shared loaders for the w8-c1 tests.
import * as path from "path";
import { loadExport, loadInventory } from "../src/io";
import { Inventory } from "../src/types";

export const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
export const devExport = () => loadExport(path.join(root, "export/dev"));
export const env = (name: string): Inventory => loadInventory(path.join(root, "envs", `${name}.json`));
export const parse = (s: string) => JSON.parse(s);
