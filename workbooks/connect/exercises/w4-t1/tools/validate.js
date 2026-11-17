"use strict";
// Migration validation harness (provided). For each test call (a UTC timestamp + key presses),
// runs the legacy vector in CM local time and the migrated Connect flow with hours evaluated from
// the exported Connect config, and reports mismatches.
//   node tools/validate.js [--dates 2026-10-09,2026-10-12] [--json]
const fs = require("fs");
const path = require("path");
const { simulate } = require("connect-kit");
const { toLocal, isOpen } = require("./hours");
const { parseVector, parseHolidayTable, runVector } = require("./avaya");

const ROOT = path.resolve(__dirname, "..");
const CM_TIME_ZONE = "America/New_York";
const read = (p) => fs.readFileSync(path.join(ROOT, p), "utf8");

function load(root = ROOT) {
  const r = (p) => fs.readFileSync(path.join(root, p), "utf8");
  return {
    mapping: JSON.parse(r("config/mapping.json")),
    hours: JSON.parse(r("config/hours-of-operation.json")),
    overrides: JSON.parse(r("config/hours-overrides.json")).Overrides,
    flow: JSON.parse(r("flows/helpdesk-inbound-migrated.json")),
    vector: parseVector(r("legacy/vector-14-hd-main.txt")),
    holidays: parseHolidayTable(r("legacy/holiday-table-3.txt")),
  };
}

/** UTC timestamps every 30 minutes across the given local (New York) dates. */
function callTimes(dates) {
  const out = [];
  for (const d of dates) {
    // walk UTC from (d 00:00 UTC - 6h) to (d 24:00 UTC + 6h) and keep stamps whose NY date is d
    const base = Date.parse(`${d}T00:00:00Z`);
    for (let t = base - 6 * 3600e3; t < base + 30 * 3600e3; t += 30 * 60e3) {
      const iso = new Date(t).toISOString();
      if (toLocal(iso, CM_TIME_ZONE).date === d) out.push(iso);
    }
  }
  return out;
}

function runOne(env, iso, digits, staffing) {
  const local = toLocal(iso, CM_TIME_ZONE);
  const legacy = runVector(env.vector, env.holidays, { local, digits, ...staffing }, env.mapping);
  const hoursMap = {};
  for (const h of env.hours) hoursMap[h.HoursOfOperationArn] = isOpen(h, env.overrides, iso);
  const metrics = {};
  for (const [name, arn] of Object.entries(env.mapping.queues)) {
    metrics[arn] = { NumberOfAgentsStaffed: staffing.staffed[name] || 0, NumberOfAgentsAvailable: staffing.available[name] || 0 };
  }
  const r = simulate(env.flow, { inputs: [...digits], hours: hoursMap, metrics });
  const qn = (arn) => Object.keys(env.mapping.queues).find((k) => env.mapping.queues[k] === arn) || arn;
  const fn = (arn) => Object.keys(env.mapping.flows).find((k) => env.mapping.flows[k] === arn) || arn;
  const connect =
    r.outcome === "TransferredToQueue" ? { kind: "Queued", queue: qn(r.queue), priority: r.routing.priority, prompts: r.prompts }
    : r.outcome === "TransferredToFlow" ? { kind: "Routed", flow: fn(r.flowId), prompts: r.prompts }
    : r.outcome === "Disconnected" ? { kind: "Disconnected", prompts: r.prompts }
    : { kind: "Error", detail: r.outcome, prompts: r.prompts };
  const same = JSON.stringify(legacy) === JSON.stringify(connect);
  return { iso, local, digits, legacy, connect, same };
}

const STAFFING = {
  staffed: { GeneralSupport: 4, PasswordReset: 2, VIPDesk: 1, MajorIncident: 2 },
  available: { GeneralSupport: 1, PasswordReset: 1, VIPDesk: 1, MajorIncident: 1 },
};
const DIGITS = [["2"], ["1"], ["3"], [null]];

function runSuite(dates, env = load()) {
  const results = [];
  for (const iso of callTimes(dates)) for (const d of DIGITS) results.push(runOne(env, iso, d, STAFFING));
  return results;
}

const brief = (o) => (o.kind === "Queued" ? `Queued ${o.queue} p${o.priority}` : o.kind === "Routed" ? `Routed ${o.flow}` : o.kind) + ` [last prompt: ${(o.prompts[o.prompts.length - 1] || "").slice(0, 38)}]`;

function report(results) {
  const bad = results.filter((r) => !r.same);
  const lines = [`calls: ${results.length}  match: ${results.length - bad.length}  MISMATCH: ${bad.length}`];
  for (const r of bad) lines.push(`FAIL ${r.iso} (NY ${r.local.date} ${r.local.time} ${r.local.day.slice(0, 3)}) digits=${JSON.stringify(r.digits)}  legacy: ${brief(r.legacy)}  |  connect: ${brief(r.connect)}`);
  return lines.join("\n");
}

if (require.main === module) {
  const arg = process.argv.indexOf("--dates");
  const dates = arg > 0 ? process.argv[arg + 1].split(",") : ["2026-10-09", "2026-10-12", "2026-10-13"];
  console.log(report(runSuite(dates)));
}

module.exports = { load, callTimes, runOne, runSuite, report, CM_TIME_ZONE, STAFFING, DIGITS };
