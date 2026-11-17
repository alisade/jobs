import { AcwSummary, EvalReference, EvalResult, Turn } from "./types";

const STOP = new Set(["the", "and", "for", "with", "that", "this", "your", "you", "their", "they", "was", "were", "has", "have", "are", "from", "into", "about", "will", "also", "can", "under", "after", "now", "its", "our", "his", "her"]);
const r2 = (n: number) => Math.round(n * 100) / 100;

function stem(w: string): string {
  if (w.length > 5 && w.endsWith("ied")) return w.slice(0, -3) + "y";
  if (w.length > 5 && w.endsWith("ing")) return w.slice(0, -3);
  if (w.length > 4 && w.endsWith("ed")) return w.slice(0, -2);
  if (w.length > 4 && w.endsWith("s") && !w.endsWith("ss")) return w.slice(0, -1);
  return w;
}

export function tokens(s: string): Set<string> {
  return new Set(
    s.toLowerCase().split(/[^a-z0-9.]+/).map((w) => w.replace(/^\.+|\.+$/g, "")).filter((w) => w.length >= 3 && !STOP.has(w)).map(stem),
  );
}

/** Identifiers that must be grounded: ticket-like ids (INC0041877, RITM0098812, E20417), versions, long numbers. */
export function identifiers(s: string): string[] {
  return [...new Set(s.match(/\b[A-Z]{1,5}\d{4,}\b|\b\d+(?:\.\d+){1,3}\b|\b\d{3,}\b/g) || [])];
}

/**
 * Deterministic faithfulness eval for an after-contact summary:
 *  - faithfulness: an actionsTaken item is supported when >= 50% of its tokens appear in one transcript turn
 *  - hallucinations: identifiers in the summary that never appear in the transcript
 *  - coverage: each key fact (list of synonyms) is present in the summary text
 *  - pass: faithfulness >= 0.8, no hallucinations, coverage >= 0.75
 */
export function evaluateSummary(summary: AcwSummary, transcript: Turn[], ref: EvalReference): EvalResult {
  const turnTokens = transcript.map((t) => tokens(t.text));
  const supported = summary.actionsTaken.filter((a) => {
    const at = [...tokens(a)];
    if (!at.length) return false;
    return turnTokens.some((tt) => at.filter((w) => tt.has(w)).length / at.length >= 0.5);
  }).length;
  const faithfulness = summary.actionsTaken.length ? r2(supported / summary.actionsTaken.length) : 1;
  const all = [summary.issue, ...summary.actionsTaken, summary.resolution, ...summary.followUps].join(" ");
  const transcriptText = transcript.map((t) => t.text).join(" ");
  const hallucinations = identifiers(all).filter((id) => !transcriptText.includes(id));
  const lower = all.toLowerCase();
  const covered = ref.keyFacts.filter((syn) => syn.some((w) => lower.includes(w.toLowerCase()))).length;
  const coverage = ref.keyFacts.length ? r2(covered / ref.keyFacts.length) : 1;
  return { faithfulness, coverage, hallucinations, pass: faithfulness >= 0.8 && hallucinations.length === 0 && coverage >= 0.75 };
}
