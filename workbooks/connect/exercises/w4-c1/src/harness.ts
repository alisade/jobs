// Migration validation harness (provided): run a Connect flow for a CallPath with connect-kit and
// normalise the result to the same Outcome shape the legacy interpreters return, so a legacy
// script and its translated flow can be compared call path by call path.
import { simulate, validateFlow, Flow } from "connect-kit";
import { CallPath, Mapping, Outcome, inWindow } from "./types";

export function hoursOpen(m: Mapping, call: CallPath): Record<string, boolean> {
  const out: Record<string, boolean> = {};
  for (const [name, arn] of Object.entries(m.hours)) {
    const model = m.hoursModel[name] || {};
    out[arn] = model.closed ? !inWindow(call.time, model.closed[0], model.closed[1]) : model.holiday ? !call.holiday : true;
  }
  return out;
}

export function runConnect(flow: Flow, call: CallPath, m: Mapping): Outcome {
  const metrics: Record<string, Record<string, number>> = {};
  for (const [name, arn] of Object.entries(m.queues)) {
    metrics[arn] = {
      NumberOfAgentsStaffed: call.staffed[name] || 0,
      NumberOfAgentsAvailable: call.available[name] || 0,
      NumberOfAgentsOnline: call.staffed[name] || 0,
    };
  }
  const r = simulate(flow, { inputs: [...call.digits], hours: hoursOpen(m, call), metrics, maxSteps: 400 });
  const queueName = (arn: string | null) => Object.keys(m.queues).find((k) => m.queues[k] === arn) || String(arn);
  const flowName = (arn?: string) => Object.keys(m.flows).find((k) => m.flows[k] === arn) || String(arn);
  switch (r.outcome) {
    case "TransferredToQueue":
      return { kind: "Queued", queue: queueName(r.queue), priority: r.routing.priority ?? NaN, prompts: r.prompts };
    case "TransferredToFlow":
      return { kind: "Routed", flow: flowName(r.flowId), prompts: r.prompts };
    case "Disconnected":
      return { kind: "Disconnected", prompts: r.prompts };
    default:
      return { kind: "Error", detail: `${r.outcome} ${r.at || ""} ${r.reason || r.error || ""}`.trim(), prompts: r.prompts };
  }
}

/** Lint errors (severity error) in a translated flow, formatted for test output. */
export function lintErrors(flow: Flow): string[] {
  return validateFlow(flow).issues.filter((i) => i.severity === "error").map((i) => `${i.code} ${i.actionId}: ${i.message}`);
}

/** Build a call path; staffing defaults to every queue staffed and available. */
export function call(over: Partial<CallPath> = {}, m?: Mapping): CallPath {
  const all = (n: number) => Object.fromEntries(Object.keys((m && m.queues) || { GeneralSupport: 1, PasswordReset: 1, VIPDesk: 1, MajorIncident: 1 }).map((k) => [k, n]));
  return { time: "10:00", holiday: false, digits: [], staffed: all(2), available: all(1), ...over };
}

/** The standard staffing variants the validation suite runs every path under. */
export function staffingVariants(m: Mapping): { label: string; staffed: Record<string, number>; available: Record<string, number> }[] {
  const names = Object.keys(m.queues);
  const with0 = (n: string, v: number, base: number) => Object.fromEntries(names.map((k) => [k, k === n ? v : base]));
  const out = [{ label: "all staffed+available", staffed: with0("", 0, 2), available: with0("", 0, 1) }];
  out.push({ label: "nobody available", staffed: with0("", 0, 2), available: with0("", 0, 0) });
  out.push({ label: "nobody staffed", staffed: with0("", 0, 0), available: with0("", 0, 0) });
  for (const n of names) out.push({ label: `${n} unstaffed`, staffed: with0(n, 0, 2), available: with0(n, 0, 1) });
  return out;
}
