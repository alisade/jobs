// Five9 IVR script -> Connect flow (reference solution).
import type { Flow } from "connect-kit";
import { parseFive9, parseSchedule } from "../legacy/five9";
import { Mapping } from "../types";
import { Emitter } from "./common";
import { FlowBuilder } from "../flowBuilder";

export function translateFive9(source: string, m: Mapping): Flow {
  const s = parseFive9(source);
  const e = new Emitter();
  const ids = new Map<string, string>();
  const resolve = (id: string | undefined): string => {
    if (!id) return e.disconnect;
    const x = s.modules.get(id);
    if (!x) throw new Error(`${s.name}: missing module ${id}`);
    if (x.type === "Hangup") return e.disconnect;
    if (!ids.has(id)) ids.set(id, e.b.id(`${id}-${x.type}`));
    return ids.get(id)!;
  };
  const text = (p?: string) => {
    const t = m.prompts[String(p)];
    if (t === undefined) throw new Error(`prompt ${p} missing from mapping`);
    return t;
  };

  for (const x of s.modules.values()) {
    const self = resolve(x.id);
    if (self !== ids.get(x.id)) continue;
    switch (x.type) {
      case "IfElse":
        e.hours(m.hours[m.five9.schedules[parseSchedule(String(x.condition))]], resolve(x.true), resolve(x.false), self);
        break;
      case "Play":
        e.message(text(x.prompt), resolve(x.next), self);
        break;
      case "Menu": {
        const ask = e.b.id(`${x.id}-menu`);
        e.b.add(
          "Loop",
          { LoopCount: String(Number(x.maxAttempts || 1)) },
          {
            Conditions: [
              { NextAction: ask, Condition: { Operator: "Equals", Operands: ["ContinueLooping"] } },
              { NextAction: resolve(x.noMatch), Condition: { Operator: "Equals", Operands: ["DoneLooping"] } },
            ],
          },
          self,
        );
        e.b.add(
          "GetParticipantInput",
          { Text: text(x.prompt), StoreInput: "False", InputTimeLimitSeconds: "5" },
          {
            Conditions: x.branches.map((b) => ({ NextAction: resolve(b.next), Condition: { Operator: "Equals", Operands: [b.digit] } })),
            Errors: FlowBuilder.errors(["InputTimeLimitExceeded", "NoMatchingCondition", "NoMatchingError"], self),
          },
          ask,
        );
        break;
      }
      case "GetDigits":
        e.collect(text(x.prompt), String(x.variable || "digits"), resolve(x.next), resolve(x.failure), self);
        break;
      case "SkillTransfer":
        e.queue(m.queues[m.five9.skills[String(x.skill)]], Number(x.priority), "NumberOfAgentsStaffed", resolve(x.failure), self);
        break;
    }
  }
  return e.start({}, resolve(s.start), `Five9 ${s.name}`);
}
