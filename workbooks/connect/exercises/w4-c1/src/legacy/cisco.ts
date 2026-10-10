// Cisco Unified ICM / CVP routing script: parser and reference interpreter (provided).
// Input is a simplified XML export of a Script Editor routing script (one <Node> per script node).
// Node types and simplified semantics:
//   Start(next)                         entry point
//   Time(window="HH:MM-HH:MM", true, false)   true when the call time is inside the window
//   RunExternalScript(microapp, prompt, next, failure)
//       microapp M (menu) or GD (get digits): play prompt, collect one entry into caller_input;
//       no input -> failure. PM (play media): play prompt -> next.
//   If(expr="caller_input == V", true, false)
//   QueueToSkillGroup(skillGroup, priority, failure) / PrecisionQueue(pq, priority, failure)
//       queued when the target has staffed agents; otherwise -> failure. Priority 1 = highest.
//   Label(label)                        route to a dialed-number label (another VDN/flow)
//   End                                 release the call
import { XMLParser } from "fast-xml-parser";
import { CallPath, Mapping, Outcome, inWindow } from "../types";

export type IcmNode = {
  id: string;
  type: "Start" | "Time" | "RunExternalScript" | "If" | "QueueToSkillGroup" | "PrecisionQueue" | "Label" | "End";
  next?: string;
  true?: string;
  false?: string;
  failure?: string;
  window?: string;
  microapp?: "M" | "GD" | "PM";
  prompt?: string;
  expr?: string;
  skillGroup?: string;
  pq?: string;
  priority?: string;
  label?: string;
};
export type IcmScript = { name: string; nodes: Map<string, IcmNode>; start: string };

export function parseIcm(xml: string): IcmScript {
  const doc = new XMLParser({ ignoreAttributes: false, attributeNamePrefix: "" }).parse(xml);
  const root = doc.IcmRoutingScript;
  if (!root) throw new Error("not an IcmRoutingScript export");
  const list: IcmNode[] = ([] as any[]).concat(root.Node || []);
  const nodes = new Map<string, IcmNode>();
  for (const n of list) nodes.set(String(n.id), { ...n, id: String(n.id) });
  const start = list.find((n) => n.type === "Start");
  if (!start) throw new Error("script has no Start node");
  return { name: root.name, nodes, start: String(start.id) };
}

export function parseExpr(expr: string): { variable: string; value: string } {
  const m = /^\s*(caller_input)\s*==\s*"?([^"\s]+)"?\s*$/.exec(expr || "");
  if (!m) throw new Error(`unsupported If expression: ${expr}`);
  return { variable: m[1], value: m[2] };
}

export function runIcm(s: IcmScript, call: CallPath, m: Mapping): Outcome {
  const prompts: string[] = [];
  const digits = [...call.digits];
  let callerInput = "";
  let id: string | undefined = s.start;
  for (let guard = 0; guard < 1000; guard++) {
    const n = id ? s.nodes.get(id) : undefined;
    if (!n) return { kind: "Error", detail: `missing node ${id}`, prompts };
    switch (n.type) {
      case "Start":
        id = n.next;
        break;
      case "Time": {
        const [from, to] = String(n.window).split("-");
        id = inWindow(call.time, from, to) ? n.true : n.false;
        break;
      }
      case "RunExternalScript": {
        prompts.push(m.prompts[String(n.prompt)] ?? `<prompt ${n.prompt}>`);
        if (n.microapp === "PM") { id = n.next; break; }
        const d = digits.length ? digits.shift() : null;
        if (d == null) { id = n.failure; break; }
        callerInput = d;
        id = n.next;
        break;
      }
      case "If":
        id = callerInput === parseExpr(String(n.expr)).value ? n.true : n.false;
        break;
      case "QueueToSkillGroup":
      case "PrecisionQueue": {
        const queue = n.type === "QueueToSkillGroup" ? m.cisco.skillGroups[String(n.skillGroup)] : m.cisco.precisionQueues[String(n.pq)];
        if ((call.staffed[queue] || 0) > 0) return { kind: "Queued", queue, priority: Number(n.priority), prompts };
        id = n.failure;
        break;
      }
      case "Label":
        return { kind: "Routed", flow: m.cisco.labels[String(n.label)], prompts };
      case "End":
        return { kind: "Disconnected", prompts };
      default:
        return { kind: "Error", detail: `unsupported node type ${(n as any).type}`, prompts };
    }
  }
  return { kind: "Error", detail: "node limit (script loop)", prompts };
}
