import * as fs from "fs";
import * as path from "path";
import { simulate, Flow, FlowAction } from "connect-kit";

export const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
const J = (p: string) => JSON.parse(fs.readFileSync(path.join(root, p), "utf8"));
export const res = J("config/resources.json");
export const MOD = J("config/module-ids.json").ModuleArn as string;
export const inbound = (): Flow => J("flows/helpdesk-inbound.json");
export const moduleFlow = (): Flow => J("flows/modules/mod-recording-defaults.json");
export const rule = () => J("rules/escalation-language-live.json");
export const ANALYTICS = "UpdateContactRecordingAndAnalyticsBehavior";

export type Path = "general" | "password" | "vip" | "afterhours-outage";

/** Walk one call path through the inbound flow + module; return the effective voice analytics settings
 * (the LAST analytics block executed wins) at the moment of the queue transfer, plus the trace. */
export function effectiveAtTransfer(p: Path) {
  const Q = res.queues;
  const r = simulate(inbound(), {
    inputs: p === "general" ? ["2"] : p === "password" ? ["1"] : p === "afterhours-outage" ? ["9"] : [],
    hours: { [res.hoursOfOperation.HelpDeskHours]: p !== "afterhours-outage" },
    lambdas: {
      [res.lambdas.identifyCaller]: () => ({ employeeId: "E1", vip: p === "vip" ? "true" : "false" }),
      [res.lambdas.passwordReset]: () => ({ resetStatus: "FAILED" }),
    },
    metrics: Object.fromEntries(Object.values(Q).map((q: any) => [q, { NumberOfAgentsStaffed: 2 }])),
    modules: { [MOD]: moduleFlow() },
  });
  const defs = new Map<string, FlowAction>();
  for (const a of inbound().Actions) defs.set(`main:${a.Identifier}`, a);
  for (const a of moduleFlow().Actions) defs.set(`mod:${a.Identifier}`, a);
  let last: any = null;
  let moduleBeforeTransfer = false;
  for (const t of r.trace) {
    const a = defs.get(`${t.module ? "mod" : "main"}:${t.id}`);
    if (t.module) moduleBeforeTransfer = true;
    if (a && a.Type === ANALYTICS && !String(t.branch).startsWith("Error")) last = a.Parameters;
  }
  return { result: r, analytics: last ? last.VoiceBehavior : null, moduleBeforeTransfer };
}
