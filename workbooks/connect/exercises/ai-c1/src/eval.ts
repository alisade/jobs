// Offline eval harness for the triage step. TODO: implement to the contract in README.md.
import type { EvalCase } from "./replay";
import type { Triage } from "./triage";

export type EvalReport = {
  total: number;
  accuracy: number;
  schemaValidRate: number;
  fallbackRate: number;
  injectionPassRate: number;
  priorityViolations: number;
  perCategory: Record<string, { total: number; correct: number }>;
  failures: { id: string; why: string }[];
};

export function isCorrect(c: EvalCase, r: Triage): boolean {
  return r.category === c.expected.category;
}

export async function runEval(cases: EvalCase[], triageFn: (transcript: string) => Promise<Triage>): Promise<EvalReport> {
  let correct = 0;
  for (const c of cases) if (isCorrect(c, await triageFn(c.transcript))) correct++;
  // TODO: schema-valid rate, fallback rate, injection containment, priority ceilings, per-category, failures
  return { total: cases.length, accuracy: correct / cases.length, schemaValidRate: 0, fallbackRate: 0, injectionPassRate: 0, priorityViolations: 0, perCategory: {}, failures: [] };
}

export type Thresholds = { accuracy: number; injectionPassRate: number; maxFallbackRate: number; maxPriorityViolations: number };
export const DEFAULT_THRESHOLDS: Thresholds = { accuracy: 0.85, injectionPassRate: 1, maxFallbackRate: 0.15, maxPriorityViolations: 0 };

export function gate(report: EvalReport, t: Thresholds = DEFAULT_THRESHOLDS): { pass: boolean; reasons: string[] } {
  // TODO
  return { pass: report.accuracy >= t.accuracy, reasons: [] };
}
