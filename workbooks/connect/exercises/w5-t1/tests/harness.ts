import * as fs from "fs";
import * as path from "path";
import { exportAll } from "../src/exporter";
import { retrieve } from "../src/retriever";
import { loadArticles, makeKb } from "../src/kbsim";
import { Entitlements } from "../src/types";

export const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
export const traffic = JSON.parse(fs.readFileSync(path.join(root, "data/replay-traffic.json"), "utf8"));
export const schema = JSON.parse(fs.readFileSync(path.join(root, "config/metadata-schema.json"), "utf8"));
export const callers: Record<string, Entitlements> = traffic.callers;

export function kb() {
  return makeKb(exportAll(loadArticles()));
}
export async function ask(caller: string, query: string) {
  const k = kb();
  const r = await retrieve(k.retrieveFn, query, callers[caller]);
  return { r, calls: k.calls, ids: r.results.map((x) => x.metadata.articleId) };
}
/** Articles a caller must never receive. */
export function forbidden(who: Entitlements, meta: Record<string, string>): boolean {
  if (meta.status !== "published") return true;
  if (!who.callerVerified) return meta.audience !== "public-help";
  if (who.employeeType === "contractor" && !["all-workers", "contractors"].includes(meta.audience)) return true;
  if (meta.audience === "restricted" && meta.department !== who.department) return true;
  if (meta.audience === "contractors" && who.employeeType !== "contractor") return true;
  return false;
}
