// Five9 VCC IVR script: parser and reference interpreter (provided).
// Input is a simplified XML export of an IVR script (one <Module> per module).
// Module types and simplified semantics:
//   IfElse(condition="schedule:<Name> is open", true, false)
//   Play(prompt, next)
//   Menu(prompt, maxAttempts, noMatch) with <Branch digit next/>: plays the prompt and waits for one
//       key, up to maxAttempts times; a key with a branch goes there; after the last failed attempt
//       (no input or an unknown key) goes to noMatch.
//   GetDigits(prompt, variable, next, failure): one entry stored in a call variable; no input -> failure
//   SkillTransfer(skill, priority, failure): queued when the skill has staffed agents, else failure.
//       Priority 1 = highest in this export.
//   Hangup
// The script starts at the first module unless <IVRScript start="..."> names one.
import { XMLParser } from "fast-xml-parser";
import { CallPath, Mapping, Outcome, inWindow } from "../types";

export type Five9Module = {
  id: string;
  type: "IfElse" | "Play" | "Menu" | "GetDigits" | "SkillTransfer" | "Hangup";
  next?: string;
  true?: string;
  false?: string;
  failure?: string;
  noMatch?: string;
  condition?: string;
  prompt?: string;
  maxAttempts?: string;
  variable?: string;
  skill?: string;
  priority?: string;
  branches: { digit: string; next: string }[];
};
export type Five9Script = { name: string; modules: Map<string, Five9Module>; start: string };

export function parseFive9(xml: string): Five9Script {
  const doc = new XMLParser({ ignoreAttributes: false, attributeNamePrefix: "" }).parse(xml);
  const root = doc.IVRScript;
  if (!root) throw new Error("not an IVRScript export");
  const list: any[] = ([] as any[]).concat(root.Module || []);
  const modules = new Map<string, Five9Module>();
  for (const x of list) {
    const branches = ([] as any[]).concat(x.Branch || []).map((b) => ({ digit: String(b.digit), next: String(b.next) }));
    const mod: any = { ...x, id: String(x.id), branches };
    delete mod.Branch;
    modules.set(mod.id, mod);
  }
  return { name: root.name, modules, start: String(root.start || list[0].id) };
}

export function parseSchedule(cond: string): string {
  const m = /^schedule:(\S+) is open$/.exec(cond || "");
  if (!m) throw new Error(`unsupported IfElse condition: ${cond}`);
  return m[1];
}

export function runFive9(s: Five9Script, call: CallPath, m: Mapping): Outcome {
  const prompts: string[] = [];
  const digits = [...call.digits];
  let id: string | undefined = s.start;
  for (let guard = 0; guard < 1000; guard++) {
    const x = id ? s.modules.get(id) : undefined;
    if (!x) return { kind: "Error", detail: `missing module ${id}`, prompts };
    switch (x.type) {
      case "IfElse": {
        const hours = m.five9.schedules[parseSchedule(String(x.condition))];
        const model = m.hoursModel[hours];
        const open = model && model.closed ? !inWindow(call.time, model.closed[0], model.closed[1]) : !call.holiday;
        id = open ? x.true : x.false;
        break;
      }
      case "Play":
        prompts.push(m.prompts[String(x.prompt)] ?? `<prompt ${x.prompt}>`);
        id = x.next;
        break;
      case "Menu": {
        const attempts = Number(x.maxAttempts || 1);
        let to: string | undefined = x.noMatch;
        for (let a = 0; a < attempts; a++) {
          prompts.push(m.prompts[String(x.prompt)] ?? `<prompt ${x.prompt}>`);
          const d = digits.length ? digits.shift() : null;
          const b = x.branches.find((br) => br.digit === d);
          if (b) { to = b.next; break; }
        }
        id = to;
        break;
      }
      case "GetDigits": {
        prompts.push(m.prompts[String(x.prompt)] ?? `<prompt ${x.prompt}>`);
        const d = digits.length ? digits.shift() : null;
        id = d == null ? x.failure : x.next;
        break;
      }
      case "SkillTransfer": {
        const queue = m.five9.skills[String(x.skill)];
        if ((call.staffed[queue] || 0) > 0) return { kind: "Queued", queue, priority: Number(x.priority), prompts };
        id = x.failure;
        break;
      }
      case "Hangup":
        return { kind: "Disconnected", prompts };
      default:
        return { kind: "Error", detail: `unsupported module ${(x as any).type}`, prompts };
    }
  }
  return { kind: "Error", detail: "module limit (script loop)", prompts };
}
