// Shared helpers for the w4-c1 tests: load fixtures, translate, compare legacy vs Connect.
import * as fs from "fs";
import * as path from "path";
import { Mapping, CallPath, Outcome } from "../src/types";
import { runConnect, staffingVariants } from "../src/harness";

export const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
export const mapping: Mapping = JSON.parse(fs.readFileSync(path.join(root, "config/mapping.json"), "utf8"));
export const read = (p: string) => fs.readFileSync(path.isAbsolute(p) ? p : path.join(root, p), "utf8");

export const TIMES = ["10:00", "21:30", "05:59", "06:00", "19:00", "07:30", "18:00"];

export function same(a: Outcome, b: Outcome): boolean {
  if (a.kind !== b.kind) return false;
  if (JSON.stringify(a.prompts) !== JSON.stringify(b.prompts)) return false;
  if (a.kind === "Queued" && b.kind === "Queued") return a.queue === b.queue && a.priority === b.priority;
  if (a.kind === "Routed" && b.kind === "Routed") return a.flow === b.flow;
  return a.kind !== "Error";
}

const brief = (o: Outcome) =>
  o.kind === "Queued" ? `Queued(${o.queue}, pri ${o.priority})` : o.kind === "Routed" ? `Routed(${o.flow})` : o.kind === "Error" ? `Error(${o.detail})` : "Disconnected";

/** Compare legacy and Connect over every time x holiday x staffing variant for one digit sequence. */
export function mismatches(
  legacy: (c: CallPath) => Outcome,
  flow: any,
  digits: (string | null)[],
  opts: { times?: string[]; holidays?: boolean[] } = {},
): string[] {
  const out: string[] = [];
  for (const time of opts.times || TIMES)
    for (const holiday of opts.holidays || [false, true])
      for (const st of staffingVariants(mapping)) {
        const c: CallPath = { time, holiday, digits, staffed: st.staffed, available: st.available };
        const want = legacy(c);
        const got = runConnect(flow, c, mapping);
        if (!same(want, got)) {
          out.push(
            `time=${time} holiday=${holiday} digits=${JSON.stringify(digits)} [${st.label}]: legacy ${brief(want)} prompts=${JSON.stringify(want.prompts)} | connect ${brief(got)} prompts=${JSON.stringify(got.prompts)}`,
          );
        }
      }
  return out;
}
