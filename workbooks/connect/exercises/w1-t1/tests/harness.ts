// Scenario builder for the w1-t1 tests: replays one caller through flows/helpdesk-inbound.json.
import * as fs from "fs";
import * as path from "path";
import { simulate, Flow } from "connect-kit";

export const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
export const res = JSON.parse(fs.readFileSync(path.join(root, "config/resources.json"), "utf8"));
export const Q = res.queues as Record<string, string>;
export const loadFlow = (): Flow => JSON.parse(fs.readFileSync(path.join(root, "flows/helpdesk-inbound.json"), "utf8"));

export function call(o: { option?: string; vip?: boolean; reset?: string; staffed?: Partial<Record<string, number>> } = {}) {
  const staffed: Record<string, number> = { GeneralSupport: 9, PasswordReset: 3, VIPDesk: 2, MajorIncident: 2, ...(o.staffed as any) };
  const r = simulate(loadFlow(), {
    inputs: [o.option || "2"],
    hours: { [res.hoursOfOperation.HelpDeskHours]: true },
    lambdas: {
      [res.lambdas.identifyCaller]: () => ({ employeeId: "E10442", vip: o.vip ? "true" : "false" }),
      [res.lambdas.passwordReset]: () => ({ resetStatus: o.reset || "FAILED" }),
    },
    metrics: Object.fromEntries(Object.entries(Q).map(([k, arn]) => [arn, { NumberOfAgentsStaffed: staffed[k] }])),
    maxSteps: 300,
  });
  return { ...r, queueName: r.queue ? Object.keys(Q).find((k) => Q[k] === r.queue) : null };
}
