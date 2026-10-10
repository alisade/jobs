// Shared types for the legacy interpreters, the translators and the tests.
import type { Flow } from "connect-kit";

export type Mapping = {
  queues: Record<string, string>;
  hours: Record<string, string>;
  hoursModel: Record<string, { closed?: [string, string]; holiday?: boolean }>;
  flows: Record<string, string>;
  prompts: Record<string, string>;
  avaya: {
    skills: Record<string, string>;
    priority: Record<string, number>;
    holidayTables: Record<string, string>;
    timeWindows: Record<string, string>;
    numbers: Record<string, string>;
  };
  cisco: {
    skillGroups: Record<string, string>;
    precisionQueues: Record<string, string>;
    timeWindows: Record<string, string>;
    labels: Record<string, string>;
  };
  five9: { skills: Record<string, string>; schedules: Record<string, string> };
};

/** One test call path, expressed in Connect terms (queue names from mapping.queues). */
export type CallPath = {
  time: string; // "HH:MM" local time of the call
  holiday: boolean; // today is in the holiday table / hours override
  digits: (string | null)[]; // caller key presses in order; null = no input (timeout)
  staffed: Record<string, number>; // queue name -> staffed agents
  available: Record<string, number>; // queue name -> available agents
};

/** What happened to the call, in comparable terms. */
export type Outcome =
  | { kind: "Queued"; queue: string; priority: number; prompts: string[] }
  | { kind: "Routed"; flow: string; prompts: string[] }
  | { kind: "Disconnected"; prompts: string[] }
  | { kind: "Error"; detail: string; prompts: string[] };

export type Translator = (source: string, mapping: Mapping) => Flow;

/** "HH:MM" inside [from, to), wrapping midnight when from > to. */
export function inWindow(time: string, from: string, to: string): boolean {
  if (from <= to) return time >= from && time < to;
  return time >= from || time < to;
}
