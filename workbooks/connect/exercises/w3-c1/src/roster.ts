// On-call roster lookup. Works as shipped; uses the call's start time (not the wall clock) so a
// retried or replayed invocation resolves the same engineer.
import * as fs from "fs";
import * as path from "path";

export interface Roster {
  timezone: string;
  hotlineNumber: string;
  helpDeskNumber: string;
  shifts: { name: string; days: number[]; start: string; end: string; primary: string; secondary: string }[];
}

export const roster: Roster = JSON.parse(fs.readFileSync(path.join(__dirname, "../config/oncall-roster.json"), "utf8"));

function localParts(epochMs: number, tz: string): { day: number; minutes: number } {
  const f = new Intl.DateTimeFormat("en-US", { timeZone: tz, weekday: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
  const parts = Object.fromEntries(f.formatToParts(new Date(epochMs)).map((p) => [p.type, p.value]));
  const day = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].indexOf(parts.weekday);
  return { day, minutes: Number(parts.hour) * 60 + Number(parts.minute) };
}

const toMin = (hhmm: string) => Number(hhmm.slice(0, 2)) * 60 + Number(hhmm.slice(3, 5));

/** The engineers on call at the given instant: { shift, primary, secondary } (E.164). */
export function onCallAt(epochMs: number): { shift: string; primary: string; secondary: string } {
  const { day, minutes } = localParts(epochMs, roster.timezone);
  const s = roster.shifts.find((x) => x.days.includes(day) && minutes >= toMin(x.start) && minutes < toMin(x.end));
  if (!s) throw new Error(`no on-call shift covers day ${day} minute ${minutes}`);
  return { shift: s.name, primary: s.primary, secondary: s.secondary };
}
