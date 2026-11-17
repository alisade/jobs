// Walk one contact through the flow with the local interpreter and print the trace.
// make simulate INPUTS='1' OPEN=true VIP=false IDENTIFY=ok|timeout RESET=SENT|FAILED STAFFED=1
const k = require("connect-kit");
const res = require("../config/resources.json");
const flow = require("../flows/helpdesk-inbound.json");
const env = process.env;
const r = k.simulate(flow, {
  inputs: (env.INPUTS || "").split(",").filter((x) => x !== "").map((x) => (x === "-" ? null : x)),
  hours: { [res.hoursOfOperation.HelpDeskHours]: env.OPEN !== "false" },
  lambdas: {
    [res.lambdas.identifyCaller]: () => (env.IDENTIFY === "timeout" ? { __error: "timeout" } : { employeeId: "E10442", vip: env.VIP === "true" ? "true" : "false", department: "Finance" }),
    [res.lambdas.passwordReset]: () => ({ resetStatus: env.RESET || "SENT" }),
  },
  metrics: Object.fromEntries(Object.values(res.queues).map((q) => [q, { NumberOfAgentsStaffed: Number(env.STAFFED || 1) }])),
});
for (const t of r.trace) console.log(`${t.id.padEnd(24)} ${t.type.padEnd(30)} ${t.branch}`);
console.log("prompts:", r.prompts);
console.log("outcome:", r.outcome, "queue:", (r.queue || "").split("/").pop(), "routing:", JSON.stringify(r.routing), r.reason || "");
