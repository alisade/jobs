"use strict";
// Avaya CM vector reference interpreter (provided; the environment, not the suspect).
// Semantics as in the Week 4 notes: time-of-day and holiday tables are evaluated in the CM's
// local time (LFG's CM runs on America/New_York); queue-to needs staffed agents, check needs
// available agents; a failed queue step falls through.
function parseVector(text) {
  const steps = [];
  for (const raw of text.split(/\r?\n/)) {
    const m = /^\s*(\d{2})\s+(\S.*?)\s*$/.exec(raw);
    if (m) steps.push({ n: Number(m[1]), s: m[2].replace(/\s+/g, " ") });
  }
  return steps;
}

function parseHolidayTable(text) {
  const out = [];
  for (const raw of text.split(/\r?\n/)) {
    const m = /^\s*(\d\d)\s+(\d\d)\s+\d\d\s+\d\d\s+(\d\d)\s+(\d\d)\s+\d\d\s+\d\d\s+(.*)$/.exec(raw);
    if (m) out.push({ from: `${m[1]}-${m[2]}`, to: `${m[3]}-${m[4]}`, name: m[5].trim() });
  }
  return out;
}

const inWindow = (t, from, to) => (from <= to ? t >= from && t < to : t >= from || t < to);

/** call = { local: {date, time}, digits: [], staffed: {queue: n}, available: {queue: n} } */
function runVector(steps, holidays, call, m) {
  const prompts = [];
  const text = (id) => m.prompts[id] || `<prompt ${id}>`;
  const q = (skill) => m.avaya.skills[skill];
  const md = call.local.date.slice(5);
  const holiday = holidays.some((h) => md >= h.from && md <= h.to);
  const digits = [...(call.digits || [])];
  let collected = "";
  const idx = new Map(steps.map((s, i) => [s.n, i]));
  let i = 0;
  for (let guard = 0; guard < 500; guard++) {
    const st = steps[i];
    if (!st) return { kind: "Disconnected", prompts };
    const s = st.s;
    let x;
    let next = i + 1;
    if ((x = /^announcement (\S+)$/.exec(s))) prompts.push(text(x[1]));
    else if ((x = /^collect \d+ digits after announcement (\S+)/.exec(s))) {
      prompts.push(text(x[1]));
      const d = digits.length ? digits.shift() : null;
      collected = d == null ? "" : d;
    } else if ((x = /^goto step (\d+) if (.+)$/.exec(s))) {
      const c = x[2];
      let hit = false;
      let y;
      if (c === "unconditionally") hit = true;
      else if ((y = /^holiday (not )?in table \d+$/.exec(c))) hit = holiday !== !!y[1];
      else if ((y = /^time-of-day is all (\d\d:\d\d) to all (\d\d:\d\d)$/.exec(c))) hit = inWindow(call.local.time, y[1], y[2]);
      else if ((y = /^digits = (\S+)$/.exec(c))) hit = collected === y[1];
      else throw new Error(`unsupported condition ${c}`);
      if (hit) next = idx.get(Number(x[1]));
    } else if ((x = /^queue-to skill (\S+) pri ([tlmh])$/.exec(s))) {
      if ((call.staffed[q(x[1])] || 0) > 0) return { kind: "Queued", queue: q(x[1]), priority: m.avaya.priority[x[2]], prompts };
    } else if ((x = /^check skill (\S+) pri ([tlmh]) if available-agents > 0$/.exec(s))) {
      if ((call.available[q(x[1])] || 0) > 0) return { kind: "Queued", queue: q(x[1]), priority: m.avaya.priority[x[2]], prompts };
    } else if ((x = /^route-to number (\S+)/.exec(s))) return { kind: "Routed", flow: m.avaya.numbers[x[1]], prompts };
    else if ((x = /^disconnect after announcement (\S+)$/.exec(s))) {
      if (x[1] !== "none") prompts.push(text(x[1]));
      return { kind: "Disconnected", prompts };
    } else if (s === "stop" || s === "busy") return { kind: "Disconnected", prompts };
    else if (!/^wait-time/.test(s)) throw new Error(`unsupported step ${s}`);
    i = next;
  }
  return { kind: "Error", prompts };
}

module.exports = { parseVector, parseHolidayTable, runVector };
