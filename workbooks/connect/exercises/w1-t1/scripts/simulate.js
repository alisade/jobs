// Replay one caller through your working copy of the flow and print the trace.
const k = require("connect-kit");
const res = require("../config/resources.json");
const flow = require("../flows/helpdesk-inbound.json");
const env = process.env;
const n = (v, d) => (v === undefined ? d : Number(v));
const Q = res.queues;
const r = k.simulate(flow, {
  inputs: (env.INPUTS || "2").split(","),
  hours: { [res.hoursOfOperation.HelpDeskHours]: env.OPEN !== "false" },
  lambdas: {
    [res.lambdas.identifyCaller]: () => ({ employeeId: "E10442", vip: env.VIP === "true" ? "true" : "false" }),
    [res.lambdas.passwordReset]: () => ({ resetStatus: env.RESET || "FAILED" }),
  },
  metrics: {
    [Q.GeneralSupport]: { NumberOfAgentsStaffed: n(env.GS_STAFFED, 9) },
    [Q.PasswordReset]: { NumberOfAgentsStaffed: n(env.PR_STAFFED, 0) },
    [Q.VIPDesk]: { NumberOfAgentsStaffed: n(env.VIP_STAFFED, 2) },
    [Q.MajorIncident]: { NumberOfAgentsStaffed: n(env.MI_STAFFED, 2) },
  },
  maxSteps: 120,
});
for (const t of r.trace.slice(0, 60)) console.log(`${t.id.padEnd(26)} ${t.type.padEnd(28)} ${t.branch}`);
if (r.trace.length > 60) console.log(`... ${r.trace.length - 60} more steps`);
console.log("outcome:", r.outcome, "queue:", (r.queue || "").split("/").pop(), r.reason || "");
