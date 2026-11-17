// Avaya Aura Communication Manager call vector: parser and reference interpreter (provided).
// Input is the text of `display vector N` (header lines are ignored; step lines are "NN <step>").
// Simplified semantics used by the migration team's validation harness:
//  - queue-to / check succeed only when the skill has staffed (queue-to) or available (check
//    ... if available-agents > 0) agents; on success the call is queued and the walk ends (in-queue
//    treatment after that point runs in a Connect customer queue flow and is out of scope).
//    A failed queue-to / check falls through to the next step.
//  - collect stores the digits for later "goto ... if digits = D" steps; no input stores "".
//  - stop, busy, disconnect and running off the last step end the call.
import { CallPath, Mapping, Outcome, inWindow } from "../types";

export type VectorStep =
  | { n: number; op: "announcement"; prompt: string }
  | { n: number; op: "goto"; target: number; cond: VectorCond }
  | { n: number; op: "collect"; digits: number; prompt: string }
  | { n: number; op: "queue-to"; skill: string; pri: string }
  | { n: number; op: "check"; skill: string; pri: string; cond: "available" | "unconditionally" }
  | { n: number; op: "wait-time"; secs: number; hearing: string }
  | { n: number; op: "route-to"; number: string }
  | { n: number; op: "disconnect"; prompt: string | null }
  | { n: number; op: "busy" }
  | { n: number; op: "stop" };

export type VectorCond =
  | { type: "unconditionally" }
  | { type: "holiday"; table: string; negate: boolean }
  | { type: "time-of-day"; window: string; from: string; to: string }
  | { type: "digits"; value: string }
  | { type: "agents"; metric: "available" | "staffed"; skill: string; gt: number };

export type Vector = { number: string; name: string; steps: VectorStep[] };

export function parseVector(text: string): Vector {
  const number = (/Number:\s*(\d+)/.exec(text) || [])[1] || "";
  const name = ((/Name:\s*(.+?)\s*$/m.exec(text) || [])[1] || "").trim();
  const steps: VectorStep[] = [];
  for (const raw of text.split(/\r?\n/)) {
    const m = /^\s*(\d{2})\s+(\S.*?)\s*$/.exec(raw);
    if (!m) continue;
    const n = Number(m[1]);
    const s = m[2].replace(/\s+/g, " ");
    let x: RegExpExecArray | null;
    if ((x = /^announcement (\S+)$/.exec(s))) steps.push({ n, op: "announcement", prompt: x[1] });
    else if ((x = /^goto step (\d+) if (.+)$/.exec(s))) steps.push({ n, op: "goto", target: Number(x[1]), cond: parseCond(x[2], n) });
    else if ((x = /^collect (\d+) digits after announcement (\S+)(?: for \S+)?$/.exec(s))) steps.push({ n, op: "collect", digits: Number(x[1]), prompt: x[2] });
    else if ((x = /^queue-to skill (\S+) pri ([tlmh])$/.exec(s))) steps.push({ n, op: "queue-to", skill: x[1], pri: x[2] });
    else if ((x = /^check skill (\S+) pri ([tlmh]) if (available-agents > 0|unconditionally)$/.exec(s))) steps.push({ n, op: "check", skill: x[1], pri: x[2], cond: x[3] === "unconditionally" ? "unconditionally" : "available" });
    else if ((x = /^wait-time (\d+) secs hearing (\S+)$/.exec(s))) steps.push({ n, op: "wait-time", secs: Number(x[1]), hearing: x[2] });
    else if ((x = /^route-to number (\S+)(?: with cov [yn] if unconditionally)?$/.exec(s))) steps.push({ n, op: "route-to", number: x[1] });
    else if ((x = /^disconnect after announcement (\S+)$/.exec(s))) steps.push({ n, op: "disconnect", prompt: x[1] === "none" ? null : x[1] });
    else if (s === "busy") steps.push({ n, op: "busy" });
    else if (s === "stop") steps.push({ n, op: "stop" });
    else throw new Error(`vector ${number} step ${n}: unsupported step "${s}"`);
  }
  return { number, name, steps };
}

function parseCond(c: string, n: number): VectorCond {
  let x: RegExpExecArray | null;
  if (c === "unconditionally") return { type: "unconditionally" };
  if ((x = /^holiday (not )?in table (\d+)$/.exec(c))) return { type: "holiday", table: x[2], negate: !!x[1] };
  if ((x = /^time-of-day is all (\d\d:\d\d) to all (\d\d:\d\d)$/.exec(c))) return { type: "time-of-day", window: c.replace(/^time-of-day is /, ""), from: x[1], to: x[2] };
  if ((x = /^digits = (\S+)$/.exec(c))) return { type: "digits", value: x[1] };
  if ((x = /^(available|staffed)-agents in skill (\S+) > (\d+)$/.exec(c))) return { type: "agents", metric: x[1] as "available" | "staffed", skill: x[2], gt: Number(x[3]) };
  throw new Error(`step ${n}: unsupported goto condition "${c}"`);
}

/** Walk one call through the vector. */
export function runVector(v: Vector, call: CallPath, m: Mapping): Outcome {
  const prompts: string[] = [];
  const text = (id: string) => m.prompts[id] ?? `<prompt ${id}>`;
  const q = (skill: string) => m.avaya.skills[skill];
  const digits = [...call.digits];
  let collected = "";
  const byN = new Map(v.steps.map((s, i) => [s.n, i]));
  let i = 0;
  for (let guard = 0; guard < 1000; guard++) {
    const s = v.steps[i];
    if (!s) return { kind: "Disconnected", prompts };
    let next = i + 1;
    switch (s.op) {
      case "announcement":
        prompts.push(text(s.prompt));
        break;
      case "wait-time":
        break;
      case "collect": {
        prompts.push(text(s.prompt));
        const d = digits.length ? digits.shift() : null;
        collected = d == null ? "" : d;
        break;
      }
      case "goto": {
        const c = s.cond;
        let hit = false;
        if (c.type === "unconditionally") hit = true;
        else if (c.type === "holiday") hit = call.holiday !== c.negate;
        else if (c.type === "time-of-day") hit = inWindow(call.time, c.from, c.to);
        else if (c.type === "digits") hit = collected === c.value;
        else if (c.type === "agents") hit = ((c.metric === "available" ? call.available : call.staffed)[q(c.skill)] || 0) > c.gt;
        if (hit) {
          const t = byN.get(s.target);
          if (t === undefined) return { kind: "Error", detail: `goto missing step ${s.target}`, prompts };
          next = t;
        }
        break;
      }
      case "queue-to":
        if ((call.staffed[q(s.skill)] || 0) > 0) return { kind: "Queued", queue: q(s.skill), priority: m.avaya.priority[s.pri], prompts };
        break;
      case "check": {
        const ok = s.cond === "available" ? (call.available[q(s.skill)] || 0) > 0 : (call.staffed[q(s.skill)] || 0) > 0;
        if (ok) return { kind: "Queued", queue: q(s.skill), priority: m.avaya.priority[s.pri], prompts };
        break;
      }
      case "route-to":
        return { kind: "Routed", flow: m.avaya.numbers[s.number], prompts };
      case "disconnect":
        if (s.prompt) prompts.push(text(s.prompt));
        return { kind: "Disconnected", prompts };
      case "busy":
      case "stop":
        return { kind: "Disconnected", prompts };
    }
    i = next;
  }
  return { kind: "Error", detail: "step limit (vector loop)", prompts };
}
