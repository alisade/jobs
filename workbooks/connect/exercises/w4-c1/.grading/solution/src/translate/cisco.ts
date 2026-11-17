// Cisco ICM/CVP routing script -> Connect flow (reference solution).
import type { Flow } from "connect-kit";
import { IcmNode, parseExpr, parseIcm } from "../legacy/cisco";
import { Mapping } from "../types";
import { Emitter } from "./common";

export function translateCisco(source: string, m: Mapping): Flow {
  const s = parseIcm(source);
  const e = new Emitter();
  const ids = new Map<string, string>();
  const resolve = (id: string | undefined, seen = new Set<string>()): string => {
    if (!id) return e.disconnect;
    const n = s.nodes.get(id);
    if (!n) throw new Error(`${s.name}: missing node ${id}`);
    if (seen.has(id)) throw new Error(`${s.name}: Start loop`);
    seen.add(id);
    if (n.type === "Start") return resolve(n.next, seen);
    if (n.type === "End") return e.disconnect;
    if (!ids.has(id)) ids.set(id, e.b.id(`node-${id}-${n.type}`));
    return ids.get(id)!;
  };
  const text = (p?: string) => {
    const t = m.prompts[String(p)];
    if (t === undefined) throw new Error(`prompt ${p} missing from mapping`);
    return t;
  };

  for (const n of s.nodes.values() as Iterable<IcmNode>) {
    const self = resolve(n.id);
    if (self !== ids.get(n.id)) continue;
    switch (n.type) {
      case "Time": {
        const [from, to] = String(n.window).split("-");
        const arn = m.hours[m.cisco.timeWindows[`${from}-${to}`]];
        // inside the window (true branch) == hours closed
        e.hours(arn, resolve(n.false), resolve(n.true), self);
        break;
      }
      case "RunExternalScript":
        if (n.microapp === "PM") e.message(text(n.prompt), resolve(n.next), self);
        else e.collect(text(n.prompt), "caller_input", resolve(n.next), resolve(n.failure), self);
        break;
      case "If":
        e.compareEquals("$.Attributes.caller_input", parseExpr(String(n.expr)).value, resolve(n.true), resolve(n.false), self);
        break;
      case "QueueToSkillGroup":
        e.queue(m.queues[m.cisco.skillGroups[String(n.skillGroup)]], Number(n.priority), "NumberOfAgentsStaffed", resolve(n.failure), self);
        break;
      case "PrecisionQueue":
        e.queue(m.queues[m.cisco.precisionQueues[String(n.pq)]], Number(n.priority), "NumberOfAgentsStaffed", resolve(n.failure), self);
        break;
      case "Label":
        e.transferToFlow(m.flows[m.cisco.labels[String(n.label)]], e.disconnect, self);
        break;
    }
  }
  return e.start({ caller_input: "" }, resolve(s.start), `ICM ${s.name}`);
}
