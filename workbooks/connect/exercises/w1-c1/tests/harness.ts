// Shared scenario builder for the w1-c1 tests: loads the flow under test and the resource ARNs.
import * as fs from "fs";
import * as path from "path";
import { simulate, Scenario, SimResult, Flow } from "connect-kit";

export const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
export const res = JSON.parse(fs.readFileSync(path.join(root, "config/resources.json"), "utf8"));
export const loadFlow = (): Flow => JSON.parse(fs.readFileSync(path.join(root, "flows/helpdesk-inbound.json"), "utf8"));
export const Q = res.queues as Record<string, string>;
export const queueName = (arn: string | null) => (arn ? Object.keys(Q).find((k) => Q[k] === arn) || arn : null);

export type Opts = {
  open?: boolean;
  inputs?: (string | null)[];
  vip?: boolean;
  identify?: "ok" | "error" | "slow";
  reset?: "SENT" | "FAILED" | "error";
  staffed?: Partial<Record<string, number>>;
  atCapacity?: string[];
};

export function run(o: Opts = {}): SimResult & { queueName: string | null } {
  const staffed = { GeneralSupport: 3, PasswordReset: 2, VIPDesk: 1, MajorIncident: 2, ...(o.staffed || {}) };
  const scenario: Scenario = {
    inputs: o.inputs || [],
    hours: { [res.hoursOfOperation.HelpDeskHours]: o.open !== false },
    lambdas: {
      [res.lambdas.identifyCaller]: () =>
        o.identify === "error" ? { __error: "Task timed out after 3.00 seconds" } : { employeeId: "E10442", vip: o.vip ? "true" : "false", department: "Finance" },
      [res.lambdas.passwordReset]: () => (o.reset === "error" ? { __error: "Unhandled" } : { resetStatus: o.reset || "SENT" }),
    },
    lambdaLatencyMs: { [res.lambdas.identifyCaller]: o.identify === "slow" ? 4500 : 400, [res.lambdas.passwordReset]: 1200 },
    metrics: Object.fromEntries(Object.entries(Q).map(([k, arn]) => [arn, { NumberOfAgentsStaffed: (staffed as any)[k] ?? 0 }])),
    queueAtCapacity: Object.fromEntries((o.atCapacity || []).map((k) => [Q[k], true])),
  };
  const r = simulate(loadFlow(), scenario);
  return { ...r, queueName: queueName(r.queue) };
}
