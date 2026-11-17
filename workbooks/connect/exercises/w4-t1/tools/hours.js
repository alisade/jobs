"use strict";
// Hours of operation evaluator used by the migration-validation harness (provided; part of the
// environment, not the suspect). Models Connect hours of operation: a TimeZone (IANA name), a
// weekly Config of {Day, StartTime, EndTime} in that time zone, and overrides that replace the
// weekly config for local dates EffectiveFrom..EffectiveTill (an empty override Config = closed).
const DAYS = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"];

/** Convert an ISO UTC timestamp to local date/day/time in an IANA time zone. Throws on a bad zone. */
function toLocal(isoUtc, timeZone) {
  const fmt = new Intl.DateTimeFormat("en-US", {
    timeZone, hourCycle: "h23", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", weekday: "long",
  });
  const parts = Object.fromEntries(fmt.formatToParts(new Date(isoUtc)).map((p) => [p.type, p.value]));
  return {
    date: `${parts.year}-${parts.month}-${parts.day}`,
    day: String(parts.weekday).toUpperCase(),
    time: `${parts.hour}:${parts.minute}`,
  };
}

const hhmm = (t) => `${String(t.Hours).padStart(2, "0")}:${String(t.Minutes).padStart(2, "0")}`;

function inConfig(config, local) {
  return (config || []).some((c) => {
    if (c.Day !== local.day) return false;
    const start = hhmm(c.StartTime);
    const end = hhmm(c.EndTime);
    if (end === "23:59") return local.time >= start;
    return local.time >= start && local.time < end;
  });
}

/** Is the hours resource open at isoUtc? */
function isOpen(hours, overrides, isoUtc) {
  if (!DAYS.length) return false;
  const local = toLocal(isoUtc, hours.TimeZone);
  const ov = (overrides || []).find((o) => o.HoursOfOperationId === hours.HoursOfOperationId && local.date >= o.EffectiveFrom && local.date <= o.EffectiveTill);
  if (ov) return inConfig(ov.Config, local);
  return inConfig(hours.Config, local);
}

module.exports = { toLocal, isOpen, DAYS };
