import { AcwSummary, EvalReference, EvalResult, Turn } from "./types";

/**
 * TODO: deterministic faithfulness eval (README "Eval"):
 *  - faithfulness: share of actionsTaken items with >= 50% of their tokens in a single transcript turn
 *    (tokens: lower case, split on non [a-z0-9.], length >= 3, minus stop words, light stemming)
 *  - hallucinations: identifiers (INC0041877, RITM0098812, E20417, 6.2.3, 3+ digit numbers) in the
 *    summary that never appear in the transcript
 *  - coverage: share of reference key facts (synonym lists) present in the summary text
 *  - pass: faithfulness >= 0.8, no hallucinations, coverage >= 0.75 (round scores to 2 decimals)
 */
export function evaluateSummary(summary: AcwSummary, transcript: Turn[], ref: EvalReference): EvalResult {
  throw new Error(`TODO: evaluateSummary (${summary.actionsTaken.length} actions, ${transcript.length} turns, ${ref.keyFacts.length} facts)`);
}
