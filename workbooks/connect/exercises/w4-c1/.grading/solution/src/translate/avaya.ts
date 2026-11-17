// Avaya CM vector -> Connect flow (reference solution).
import type { Flow } from "connect-kit";
import { parseVector, VectorStep } from "../legacy/avaya";
import { Mapping } from "../types";
import { Emitter } from "./common";

export function translateAvaya(source: string, m: Mapping): Flow {
  const v = parseVector(source);
  const e = new Emitter();
  const index = new Map(v.steps.map((s, i) => [s.n, i]));
  const ids = new Map<number, string>();
  const at = (n: number) => {
    const i = index.get(n);
    if (i === undefined) throw new Error(`vector ${v.number}: goto to missing step ${n}`);
    return i;
  };

  // Steps that emit nothing resolve to whatever they lead to.
  const resolve = (i: number, seen = new Set<number>()): string => {
    const s = v.steps[i];
    if (!s) return e.disconnect;
    if (seen.has(i)) throw new Error(`vector ${v.number}: unconditional goto loop at step ${s.n}`);
    seen.add(i);
    if (s.op === "goto" && s.cond.type === "unconditionally") return resolve(at(s.target), seen);
    if (s.op === "wait-time") return resolve(i + 1, seen);
    if (s.op === "busy" || s.op === "stop" || (s.op === "disconnect" && !s.prompt)) return e.disconnect;
    if (!ids.has(i)) ids.set(i, e.b.id(`step-${String(s.n).padStart(2, "0")}-${s.op}`));
    return ids.get(i)!;
  };
  const text = (id: string) => {
    const t = m.prompts[id];
    if (t === undefined) throw new Error(`announcement ${id} has no prompt text in the mapping`);
    return t;
  };
  const queueArn = (skill: string) => m.queues[m.avaya.skills[skill]];

  v.steps.forEach((s: VectorStep, i) => {
    const self = resolve(i);
    if (self !== ids.get(i)) return; // alias step: nothing to emit
    const next = resolve(i + 1);
    switch (s.op) {
      case "announcement":
        e.message(text(s.prompt), next, self);
        break;
      case "collect": {
        const clear = e.setAttributes({ digits: "" }, next);
        e.collect(text(s.prompt), "digits", next, clear, self);
        break;
      }
      case "goto": {
        const target = resolve(at(s.target));
        const c = s.cond;
        if (c.type === "holiday") {
          const arn = m.hours[m.avaya.holidayTables[c.table]];
          // holiday hours are closed (False) on a holiday
          e.hours(arn, c.negate ? target : next, c.negate ? next : target, self);
        } else if (c.type === "time-of-day") {
          e.hours(m.hours[m.avaya.timeWindows[c.window]], next, target, self);
        } else if (c.type === "digits") {
          e.compareEquals("$.Attributes.digits", c.value, target, next, self);
        } else if (c.type === "agents") {
          if (c.gt !== 0) throw new Error(`step ${s.n}: Connect agent checks only support "> 0"`);
          e.agentsCheck(queueArn(c.skill), c.metric === "available" ? "NumberOfAgentsAvailable" : "NumberOfAgentsStaffed", target, next, self);
        }
        break;
      }
      case "queue-to":
        e.queue(queueArn(s.skill), m.avaya.priority[s.pri], "NumberOfAgentsStaffed", next, self);
        break;
      case "check":
        e.queue(queueArn(s.skill), m.avaya.priority[s.pri], s.cond === "available" ? "NumberOfAgentsAvailable" : "NumberOfAgentsStaffed", next, self);
        break;
      case "route-to":
        e.transferToFlow(m.flows[m.avaya.numbers[s.number]], next, self);
        break;
      case "disconnect":
        e.message(text(s.prompt!), e.disconnect, self);
        break;
    }
  });
  return e.start({ digits: "" }, resolve(0), `Vector ${v.number} ${v.name}`);
}
